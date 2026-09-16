"""
agent.py — Agentic Research Assistant using LangGraph.

NEW vs Lecture 18 (Document Butler):
  1. LangGraph StateGraph — instead of a linear RAG chain, the agent has a
     graph of nodes (steps). Each node can make decisions and route the flow.
  2. validate_topic — NEW gate node: LLM checks if the topic is worth researching
     before spending tokens and API calls on it.
  3. structured_output — LLM returns a Pydantic object (not free text),
     so we can read fields like analysis.sub_questions programmatically.
  4. Annotated[List[str], add] — reducer pattern: multiple nodes append
     to thinking_steps without overwriting each other.
  5. Web search (Tavily) — searches the real internet, up to 20 URLs.
  6. Optional KB search — if a Qdrant knowledge base is configured, also
     searches local documents. Falls back gracefully if not configured.

Agent flow (graph):

  topic
    ↓
  [validate_topic]       ← Is this a meaningful research topic?
    ↓ (conditional edge)
    ├─ invalid → END     ← Stop early, emit error event to frontend
    └─ valid   ↓
  [analyze_query]        ← Break topic into 3 sub-questions + pick strategy
    ↓
  [decide_search_strategy]   ← Routing node
    ↓ (conditional edge)
    ├─ "web_only"  → [web_search] → [kb_search] → [synthesize]
    └─ "both"      → [web_search] → [kb_search] → [synthesize]
                     (kb_search skips automatically if Qdrant not configured)

Connection to Lecture 15 (Agentic RAG):
  In Lecture 15 the agent could RETRY and fall back to web search.
  Here the agent PLANS FIRST (validate → analyze → decide) and then executes.
  Planning before acting is a key mental model shift in agentic AI systems.
"""

import logging
import os
from operator import add
from typing import Annotated, List, Optional

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

# Maximum number of web URLs to collect in total.
# We spread this across sub-questions (up to 7 per question).
MAX_URLS = 20


# ── Structured output schemas ─────────────────────────────────────────────────
# When we call llm.with_structured_output(SomeModel), the LLM fills in
# the Pydantic fields instead of returning free text.
# This is much more reliable than parsing the LLM's text output manually.

class TopicValidation(BaseModel):
    """
    The LLM evaluates whether a topic is worth researching.
    This prevents the agent from burning API calls on gibberish or empty input.
    """
    is_valid: bool
    """True if this is a meaningful topic that a researcher could write about."""

    reason: str
    """One sentence explaining why the topic is valid or invalid."""

    refined_topic: str
    """
    If valid: a cleaned-up version of the topic (fix typos, add context).
    If invalid: return the original topic unchanged.
    """


class QueryAnalysis(BaseModel):
    """LLM fills this in to plan the research strategy."""

    sub_questions: List[str]
    """Exactly 3 focused sub-questions that together cover the topic."""

    search_strategy: str
    """
    One of: 'web_only' | 'both'.
    Use 'both' when the topic would benefit from both web results
    AND any locally indexed documents.
    """

    reasoning: str
    """Brief explanation of why this strategy was chosen."""


# ── Agent state ───────────────────────────────────────────────────────────────
# ResearchState is the shared "memory" that flows between nodes.
# Each node receives the full state and returns a PARTIAL update (a dict).
# LangGraph merges the update into the state using reducers.
#
# KEY CONCEPT — Reducer pattern:
#   thinking_steps: Annotated[List[str], add]
#
#   Without reducer:  return {"thinking_steps": ["new step"]}
#     → LangGraph REPLACES the whole list. Previous steps are lost.
#
#   With reducer (add):  return {"thinking_steps": ["new step"]}
#     → LangGraph APPENDS "new step" to the existing list.
#     The `add` function from the `operator` module concatenates lists.
#
#   This lets each node add its own steps without knowing what came before.

class ResearchState(TypedDict):
    # ── Input ────────────────────────────────────────────────────────────────
    topic: str
    override_web_search: Optional[bool]  # from HTTP request — None = let agent decide

    # ── Topic validation (set by validate_topic node) ────────────────────────
    is_valid: bool
    validation_reason: str

    # ── Planning (set by analyze_query node) ─────────────────────────────────
    sub_questions: List[str]
    search_strategy: str    # "web_only" | "both"

    # ── Search results ────────────────────────────────────────────────────────
    web_results: List[dict]     # [{title, url, content}, ...]
    vector_results: List[str]   # text chunks from local knowledge base (if configured)

    # ── Output ────────────────────────────────────────────────────────────────
    report: str                 # Final generated markdown report
    sources: List[dict]         # [{title, url, content_preview}, ...]

    # ── Streaming steps (reducer: each node appends, never replaces) ──────────
    thinking_steps: Annotated[List[str], add]


# ── Agent builder ─────────────────────────────────────────────────────────────

def build_agent(openai_api_key: str):
    """
    Build and compile the LangGraph research agent.

    This function is called ONCE at server startup (in main.py's lifespan).
    The compiled agent is stored in app_state and reused for every request —
    same pattern as how Lecture 18/19 reuse the LLM and embeddings.

    Args:
        openai_api_key — passed in from the environment, not hardcoded here.

    Returns:
        A compiled LangGraph graph ready to call .astream_events() on.
    """
    # Main LLM for synthesis and query analysis
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)

    # Structured output variants — same LLM, different output format
    # with_structured_output() tells the LLM to respond as a Pydantic object
    validation_llm = llm.with_structured_output(TopicValidation)
    analysis_llm = llm.with_structured_output(QueryAnalysis)

    # Tavily is an AI-optimized search engine with a free tier API.
    # We instantiate it here; per-query max_results is set dynamically in web_search.
    tavily_api_key = os.getenv("TAVILY_API_KEY", "")


    # ── Node 1: Validate topic ────────────────────────────────────────────────
    # This is a GATE node — it can stop the graph early if the topic is invalid.
    # The conditional edge after this node routes to either analyze_query or END.
    #
    # KEY LESSON: Adding validation before expensive operations is good practice.
    # In real systems you'd also check for offensive content, rate limits, etc.

    def validate_topic(state: ResearchState) -> dict:
        """
        Ask the LLM whether this is a meaningful research topic.
        If invalid, the graph will stop here (conditional edge routes to END).
        """
        topic = state["topic"]
        logger.info(f"Validating topic: {topic!r}")

        prompt = f"""You are a research quality controller.

Evaluate whether the following is a valid research topic that a researcher
could write a 2-page academic or professional report about.

Topic: "{topic}"

VALID examples:
  - "Impact of AI on healthcare in 2025"
  - "Climate change mitigation strategies"
  - "History of the Roman Empire"

INVALID examples:
  - "asdfgh" (gibberish / random characters)
  - Single words with no context like just "hello" or "test"
  - Completely empty or whitespace-only input
  - Offensive or harmful content

Be lenient — if there is ANY reasonable interpretation as a research topic, mark it valid.
For valid topics, also provide a refined version (fix typos, add clarity if needed).
"""
        result: TopicValidation = validation_llm.invoke(prompt)

        if result.is_valid:
            steps = [
                f'Checking topic: "{topic}"',
                f"✓ Valid research topic — {result.reason}",
            ]
            if result.refined_topic and result.refined_topic != topic:
                steps.append(f'Refined to: "{result.refined_topic}"')
            # Use the refined topic if the LLM cleaned it up
            refined = result.refined_topic if result.refined_topic else topic
        else:
            steps = [
                f'Checking topic: "{topic}"',
                f"✗ Invalid topic — {result.reason}",
            ]
            refined = topic  # Keep original even if invalid

        return {
            "is_valid": result.is_valid,
            "validation_reason": result.reason,
            "topic": refined,          # May be refined/corrected
            "thinking_steps": steps,   # Reducer appends these to the list
        }


    # ── Node 2: Analyze query ─────────────────────────────────────────────────
    # This is the PLANNING node. The LLM decides:
    #   - What 3 sub-questions cover the topic?
    #   - Should we search the web only, or also check the knowledge base?
    #
    # KEY LESSON: The LLM is not just answering a question here — it is PLANNING.
    # That shift from "answer" to "plan" is the core mental model of agentic AI.

    def analyze_query(state: ResearchState) -> dict:
        """
        Use the LLM to break the topic into sub-questions and decide search strategy.
        """
        topic = state["topic"]
        override = state.get("override_web_search")

        logger.info(f"Analyzing query: {topic!r}")

        prompt = f"""You are a research planner. Your job is to prepare a research strategy.

Topic to research: "{topic}"

Task:
1. Break the topic into exactly 3 focused sub-questions that together cover it comprehensively.
   Each sub-question should be specific and searchable.

2. Decide the search strategy:
   - "web_only":  Topic requires fresh/recent data, news, statistics, or current events.
   - "both":      Topic benefits from BOTH web sources AND locally stored documents
                  (choose this when the topic is academic, historical, or involves
                   domain knowledge that might exist in a knowledge base).

Be concise and specific in your sub-questions."""

        analysis: QueryAnalysis = analysis_llm.invoke(prompt)

        # If the user forced web search from the UI checkbox, respect that
        strategy = analysis.search_strategy
        if override is True:
            strategy = "web_only"

        steps = [
            f"Strategy chosen: {strategy}",
            f"Reason: {analysis.reasoning}",
            "Breaking topic into 3 focused sub-questions:",
            f"  Q1: {analysis.sub_questions[0]}",
            f"  Q2: {analysis.sub_questions[1]}",
            f"  Q3: {analysis.sub_questions[2]}",
        ]

        return {
            "sub_questions": analysis.sub_questions,
            "search_strategy": strategy,
            "thinking_steps": steps,
        }


    # ── Node 3: Decide search strategy (routing node) ─────────────────────────
    # This is a thin node that just logs the routing decision.
    # The ACTUAL routing happens in the conditional edge below.
    # We keep them separate so the graph is easier to read and debug.

    def decide_search_strategy(state: ResearchState) -> dict:
        """Log the search strategy. Routing is done by the conditional edge."""
        strategy = state.get("search_strategy", "web_only")
        return {
            "thinking_steps": [
                f"Search plan confirmed: {strategy}",
                f"Will search {len(state.get('sub_questions', []))} sub-question(s) — max {MAX_URLS} URLs total",
            ]
        }


    # ── Node 4: Web search ────────────────────────────────────────────────────
    # We search Tavily for each sub-question and accumulate up to MAX_URLS results.
    #
    # WHY CAP AT 20?
    #   More results = better report quality, but also:
    #   - More tokens sent to the synthesis LLM (costs money)
    #   - Slower response time
    #   20 is a reasonable balance for a teaching project.

    def web_search(state: ResearchState) -> dict:
        """
        Search Tavily for each sub-question, collecting up to MAX_URLS results total.

        KEY CHANGE vs original: we now log the EXACT query string and URL count
        per sub-question so students can see exactly what goes to the internet.
        """
        sub_questions = state.get("sub_questions", [])
        all_results = []
        steps = [f"Starting web search — cap: {MAX_URLS} URLs total"]

        for i, question in enumerate(sub_questions, 1):
            # Stop early if we've already hit the URL cap
            if len(all_results) >= MAX_URLS:
                steps.append(f"URL cap ({MAX_URLS}) reached — skipping remaining queries")
                break

            # Calculate how many results to request for this sub-question
            remaining = MAX_URLS - len(all_results)
            per_query = min(7, remaining)   # At most 7 per sub-question

            # ── Log the ACTUAL query string going to the internet ─────────────
            # This is what students need to see: the real text sent to Tavily.
            steps.append(f"🔍 Query {i}/{len(sub_questions)}: \"{question}\"")

            try:
                # Create a fresh TavilySearchResults with the correct limit.
                # We do this per-query so per_query can vary.
                tavily = TavilySearchResults(
                    max_results=per_query,
                    tavily_api_key=tavily_api_key,
                )
                results = tavily.invoke(question)

                # results is a list of dicts: [{title, url, content, score}, ...]
                if isinstance(results, list) and results:
                    all_results.extend(results)
                    # Show each URL that was found
                    steps.append(f"   ↳ {len(results)} URL(s) found (total so far: {len(all_results)})")
                    for r in results[:3]:   # Show first 3 titles for transparency
                        title = r.get("title", "")[:60]
                        steps.append(f"     • {title}")
                    if len(results) > 3:
                        steps.append(f"     • ... and {len(results) - 3} more")
                else:
                    steps.append("   ↳ No results returned for this query")

            except Exception as e:
                logger.warning(f"Tavily search failed for '{question}': {e}")
                steps.append(f"   ↳ Search failed: {str(e)[:80]}")

        steps.append(f"Web search complete — {len(all_results)} URL(s) collected")
        return {"web_results": all_results, "thinking_steps": steps}


    # ── Node 5: Knowledge base search (optional) ──────────────────────────────
    # If a Qdrant knowledge base is configured (via env vars), we also search
    # it for relevant chunks from locally uploaded documents.
    #
    # This connects back to Lecture 18/19 (RAG with Qdrant).
    # If the knowledge base is not configured, this node safely skips itself.
    #
    # KEY LESSON: Good agents are resilient. Optional integrations should
    # fail gracefully rather than crashing the whole workflow.

    def kb_search(state: ResearchState) -> dict:
        """
        Search the Qdrant knowledge base for relevant chunks.
        Skips gracefully if QDRANT_URL is not set in the environment.
        """
        qdrant_url = os.getenv("QDRANT_URL", "")

        # No knowledge base configured — skip silently
        if not qdrant_url:
            return {
                "vector_results": [],
                "thinking_steps": ["Knowledge base: not configured, skipping local search"],
            }

        topic = state["topic"]
        steps = ["Searching local knowledge base (Qdrant)..."]

        try:
            # Import here so the server still starts even if these packages
            # are not installed (they're optional for KB-less setups)
            from langchain_huggingface import HuggingFaceEmbeddings
            from qdrant_client import QdrantClient

            qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
            collection_name = os.getenv("QDRANT_COLLECTION", "rag_uploads")

            # Use the same local embedding model as Lecture 18/19
            # all-MiniLM-L6-v2 is free and runs locally — no API key needed
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

            steps.append(f"Embedding query for vector search: \"{topic[:60]}\"")

            # Embed the research topic to use as the search vector
            query_vector = embeddings.embed_query(topic)

            # Connect to Qdrant and search for the top 3 most relevant chunks
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            results = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=3,              # top 3 chunks is enough to augment the web results
                with_payload=True,
                with_vectors=False,   # we don't need the vectors back, just the text
            )

            # Extract the chunk text from each result's payload
            chunks = []
            for point in results.points:
                chunk_text = point.payload.get("chunk_text", "")
                if chunk_text:
                    chunks.append(chunk_text)

            steps.append(f"✓ Found {len(chunks)} relevant chunk(s) from knowledge base")
            return {"vector_results": chunks, "thinking_steps": steps}

        except ImportError:
            steps.append("Knowledge base packages not installed, skipping")
            return {"vector_results": [], "thinking_steps": steps}
        except Exception as e:
            logger.warning(f"KB search failed: {e}")
            steps.append(f"Knowledge base search failed: {str(e)[:80]}")
            return {"vector_results": [], "thinking_steps": steps}


    # ── Node 6: Synthesize ────────────────────────────────────────────────────
    # The "writing" node — the LLM acts as a research analyst.
    # It reads all the collected web results + KB chunks and writes
    # a structured, detailed markdown report.

    def synthesize(state: ResearchState) -> dict:
        """
        Combine all research findings into a detailed structured report.
        """
        topic = state["topic"]
        web_results = state.get("web_results", [])
        vector_results = state.get("vector_results", [])

        steps = [
            f"Combining {len(web_results)} web source(s) + {len(vector_results)} KB chunk(s)",
            "Drafting report structure: Executive Summary → Background → Findings → Analysis → Conclusion",
        ]

        # ── Build context string from web results ─────────────────────────────
        context_parts = []
        sources = []

        for result in web_results:
            content = result.get("content", "")[:600]   # Limit each snippet to 600 chars
            url = result.get("url", "")
            title = result.get("title", url)

            if content:
                context_parts.append(f"[Web Source: {title}]\n{content}")

            if url:
                sources.append({
                    "title": title,
                    "url": url,
                    "content_preview": content[:120] + "..." if len(content) > 120 else content,
                })

        # ── Add knowledge base chunks if any ─────────────────────────────────
        for chunk in vector_results:
            context_parts.append(f"[Knowledge Base]\n{chunk}")

        # Combine all context, separated by dividers for clarity
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No external sources found."

        # Build a numbered source list for the report footer
        source_list = "\n".join(
            f"{i+1}. {s['title']}\n   {s['url']}"
            for i, s in enumerate(sources)
        ) if sources else "No web sources were found."

        steps.append("Sending context to LLM for synthesis...")

        # ── Generate the report via LLM ───────────────────────────────────────
        # ChatPromptTemplate lets us keep the prompt readable as a template
        # with {placeholder} variables filled in at invoke() time.
        report_prompt = ChatPromptTemplate.from_template(
            """You are an expert research analyst. Write a comprehensive, structured research report.

Topic: {topic}

Research findings:
{context}

Write a detailed research report with this EXACT structure:

# {topic}

## Executive Summary
[2-3 sentences summarizing the key findings]

## Background & Context
[Detailed background explaining the topic, its history, and why it matters. 3-5 sentences.]

## Current State & Key Findings
[The most important and current information about the topic, backed by sources. 3-5 sentences.]

## Analysis & Implications
[Your analysis of what the findings mean, trends, and future implications. 3-5 sentences.]

## Conclusion
[Key takeaways and actionable insights. 2-3 sentences.]

## Sources
{source_list}

Requirements:
- Be specific and cite evidence from the sources
- Use professional, analytical language
- Each section must have at least 3 sentences
- Reference source titles when mentioning specific facts"""
        )

        # LCEL chain: prompt → LLM → parse output as a plain string
        chain = report_prompt | llm | StrOutputParser()
        report = chain.invoke({
            "topic": topic,
            "context": context,
            "source_list": source_list,
        })

        steps.append("✓ Report generation complete")

        return {
            "report": report,
            "sources": sources,
            "thinking_steps": steps,
        }


    # ── Routing functions ─────────────────────────────────────────────────────
    # These are NOT nodes — they are functions that tell LangGraph which
    # node to go to next. They inspect the state and return a string
    # that matches one of the keys in the conditional edge map.

    def route_after_validation(state: ResearchState) -> str:
        """
        After validate_topic:
          - If topic is valid → continue to analyze_query
          - If topic is invalid → END the graph (error will be handled by api.py)
        """
        if state.get("is_valid", False):
            return "analyze_query"
        return "__end__"   # Special LangGraph key to route to END

    def route_search(state: ResearchState) -> str:
        """
        After decide_search_strategy:
          Always go to web_search first. kb_search runs after web_search
          for ALL strategies (it skips itself if Qdrant is not configured).
        """
        # We always do web search. kb_search runs next and self-skips if not needed.
        return "web_search"


    # ── Build the graph ───────────────────────────────────────────────────────
    # StateGraph takes our state TypedDict as its schema.
    # Nodes are added with add_node(name, function).
    # Edges define the flow between nodes.

    workflow = StateGraph(ResearchState)

    # ── Add all nodes ─────────────────────────────────────────────────────────
    workflow.add_node("validate_topic", validate_topic)
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("decide_search_strategy", decide_search_strategy)
    workflow.add_node("web_search", web_search)
    workflow.add_node("kb_search", kb_search)
    workflow.add_node("synthesize", synthesize)

    # ── Set entry point ───────────────────────────────────────────────────────
    # Every request starts at validate_topic (our first node)
    workflow.set_entry_point("validate_topic")

    # ── Add edges ─────────────────────────────────────────────────────────────
    # add_conditional_edges(from_node, routing_fn, route_map)
    # The routing_fn returns a string; route_map maps strings to target nodes.

    # After validation: valid → analyze, invalid → END
    workflow.add_conditional_edges(
        "validate_topic",
        route_after_validation,
        {
            "analyze_query": "analyze_query",
            "__end__": END,
        },
    )

    # analyze_query → decide_search_strategy (always)
    workflow.add_edge("analyze_query", "decide_search_strategy")

    # decide_search_strategy → web_search (always, via routing fn)
    workflow.add_conditional_edges(
        "decide_search_strategy",
        route_search,
        {"web_search": "web_search"},
    )

    # web_search → kb_search (always — kb_search self-skips if not configured)
    workflow.add_edge("web_search", "kb_search")

    # kb_search → synthesize (always)
    workflow.add_edge("kb_search", "synthesize")

    # synthesize → END
    workflow.add_edge("synthesize", END)

    # compile() validates the graph structure and returns a runnable object
    return workflow.compile()
