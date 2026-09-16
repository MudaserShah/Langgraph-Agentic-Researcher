"""
agent.py — Agentic Research Assistant using LangGraph.

OpenAI-free version:
  - Hugging Face LLM for validation, planning, and synthesis
  - Hugging Face/local embeddings for Qdrant
  - Tavily for web search
  - LangGraph for agent orchestration
"""

import json
import logging
import os
from operator import add
from typing import Annotated, List, Optional

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

MAX_URLS = 20


# ── Structured output schemas ────────────────────────────────────────────────

class TopicValidation(BaseModel):
    is_valid: bool
    reason: str
    refined_topic: str


class QueryAnalysis(BaseModel):
    sub_questions: List[str]
    search_strategy: str
    reasoning: str


# ── Agent state ───────────────────────────────────────────────────────────────

class ResearchState(TypedDict):
    topic: str
    override_web_search: Optional[bool]

    is_valid: bool
    validation_reason: str

    sub_questions: List[str]
    search_strategy: str

    web_results: List[dict]
    vector_results: List[str]

    report: str
    sources: List[dict]

    thinking_steps: Annotated[List[str], add]


# ── Helper: parse JSON returned by Hugging Face ───────────────────────────────

def _parse_json_response(text: str) -> dict:
    """
    Extract a JSON object from an LLM response.

    Hugging Face models sometimes wrap JSON in ```json ... ``` fences.
    This helper removes those fences and extracts the JSON object safely.
    """
    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"LLM did not return valid JSON: {text[:500]}")

    json_text = text[start:end + 1]

    return json.loads(json_text)


# ── Agent builder ────────────────────────────────────────────────────────────

def build_agent(hf_token: str = ""):
    """
    Build and compile the LangGraph research agent.

    Uses Hugging Face instead of OpenAI.

    Args:
        hf_token: Hugging Face API token.

    Returns:
        Compiled LangGraph agent.
    """

    # Hugging Face token can come from argument or environment.
    hf_token = hf_token or os.getenv("HF_TOKEN", "")

    if not hf_token:
        raise ValueError(
            "HF_TOKEN is not configured. "
            "Add your Hugging Face token to the .env file."
        )

    # Hugging Face model.
    #
    # This model is instruction-tuned and can be used through
    # HuggingFaceEndpoint.
    model_name = os.getenv(
        "LLM_MODEL",
        "meta-llama/Llama-3.1-8B-Instruct",
    )

    llm_endpoint = HuggingFaceEndpoint(
        repo_id=model_name,
        huggingfacehub_api_token=hf_token,
        temperature=0.0,
        max_new_tokens=2048,
    )
    llm = ChatHuggingFace(llm=llm_endpoint)

    # Tavily
    tavily_api_key = os.getenv("TAVILY_API_KEY", "")

    # ── Node 1: Validate topic ───────────────────────────────────────────────

    def validate_topic(state: ResearchState) -> dict:
        topic = state["topic"]

        logger.info(f"Validating topic: {topic!r}")

        prompt = f"""
You are a research quality controller.

Evaluate whether the following is a valid research topic that a researcher
could write a 2-page academic or professional report about.

Topic: "{topic}"

VALID examples:
- Impact of AI on healthcare in 2025
- Climate change mitigation strategies
- History of the Roman Empire

INVALID examples:
- asdfgh
- hello
- test
- empty input
- offensive or harmful content

Be lenient. If there is any reasonable interpretation as a research topic,
mark it valid.

Return ONLY valid JSON.
Do not use markdown.
Do not add explanations outside the JSON.

Required JSON format:

{{
  "is_valid": true,
  "reason": "one sentence",
  "refined_topic": "cleaned up research topic"
}}
"""

        try:
            response = llm.invoke(prompt)

            result_data = _parse_json_response(response.content)

            result = TopicValidation(**result_data)

        except Exception as e:
            logger.warning(f"Topic validation failed: {e}")

            # Fail open for a reasonable user query.
            result = TopicValidation(
                is_valid=bool(topic.strip()),
                reason="Topic validation model failed, so the topic was checked locally.",
                refined_topic=topic.strip(),
            )

        if result.is_valid:
            steps = [
                f'Checking topic: "{topic}"',
                f"✓ Valid research topic — {result.reason}",
            ]

            refined = (
                result.refined_topic
                if result.refined_topic
                else topic
            )

            if refined != topic:
                steps.append(f'Refined to: "{refined}"')

        else:
            steps = [
                f'Checking topic: "{topic}"',
                f"✗ Invalid topic — {result.reason}",
            ]

            refined = topic

        return {
            "is_valid": result.is_valid,
            "validation_reason": result.reason,
            "topic": refined,
            "thinking_steps": steps,
        }

    # ── Node 2: Analyze query ────────────────────────────────────────────────

    def analyze_query(state: ResearchState) -> dict:
        topic = state["topic"]
        override = state.get("override_web_search")

        logger.info(f"Analyzing query: {topic!r}")

        prompt = f"""
You are a research planner.

Topic to research:
"{topic}"

Create a research strategy.

Tasks:

1. Create exactly 3 focused sub-questions.
2. Decide search strategy:
   - "web_only" for current news, recent data, statistics, or current events.
   - "both" for academic, historical, or domain knowledge topics.

Return ONLY valid JSON.
Do not use markdown.
Do not add text outside the JSON.

Required JSON format:

{{
  "sub_questions": [
    "question 1",
    "question 2",
    "question 3"
  ],
  "search_strategy": "web_only",
  "reasoning": "brief explanation"
}}
"""

        try:
            response = llm.invoke(prompt)

            result_data = _parse_json_response(response.content)

            analysis = QueryAnalysis(**result_data)

        except Exception as e:
            logger.warning(f"Query analysis failed: {e}")

            # Safe fallback so the graph can continue.
            analysis = QueryAnalysis(
                sub_questions=[
                    f"What is {topic}?",
                    f"What are the key findings and developments related to {topic}?",
                    f"What are the implications and future trends of {topic}?",
                ],
                search_strategy="web_only",
                reasoning="Fallback strategy used because LLM planning failed.",
            )

        # Validate strategy
        strategy = analysis.search_strategy

        if strategy not in ("web_only", "both"):
            strategy = "web_only"

        if override is True:
            strategy = "web_only"

        # Ensure exactly 3 questions
        questions = analysis.sub_questions[:3]

        while len(questions) < 3:
            questions.append(
                f"What else should researchers know about {topic}?"
            )

        steps = [
            f"Strategy chosen: {strategy}",
            f"Reason: {analysis.reasoning}",
            "Breaking topic into 3 focused sub-questions:",
            f"  Q1: {questions[0]}",
            f"  Q2: {questions[1]}",
            f"  Q3: {questions[2]}",
        ]

        return {
            "sub_questions": questions,
            "search_strategy": strategy,
            "thinking_steps": steps,
        }

    # ── Node 3: Decide search strategy ──────────────────────────────────────

    def decide_search_strategy(state: ResearchState) -> dict:
        strategy = state.get("search_strategy", "web_only")

        return {
            "thinking_steps": [
                f"Search plan confirmed: {strategy}",
                f"Will search {len(state.get('sub_questions', []))} "
                f"sub-question(s) — max {MAX_URLS} URLs total",
            ]
        }

    # ── Node 4: Web search ───────────────────────────────────────────────────

    def web_search(state: ResearchState) -> dict:
        sub_questions = state.get("sub_questions", [])

        all_results = []

        steps = [
            f"Starting web search — cap: {MAX_URLS} URLs total"
        ]

        if not tavily_api_key:
            steps.append(
                "Tavily API key not configured — web search skipped"
            )

            return {
                "web_results": [],
                "thinking_steps": steps,
            }

        for i, question in enumerate(sub_questions, 1):

            if len(all_results) >= MAX_URLS:
                steps.append(
                    f"URL cap ({MAX_URLS}) reached — "
                    "skipping remaining queries"
                )
                break

            remaining = MAX_URLS - len(all_results)
            per_query = min(7, remaining)

            steps.append(
                f'🔍 Query {i}/{len(sub_questions)}: "{question}"'
            )

            try:
                tavily = TavilySearchResults(
                    max_results=per_query,
                    tavily_api_key=tavily_api_key,
                )

                results = tavily.invoke(question)

                if isinstance(results, list) and results:

                    all_results.extend(results)

                    steps.append(
                        f"   ↳ {len(results)} URL(s) found "
                        f"(total so far: {len(all_results)})"
                    )

                    for result in results[:3]:
                        title = result.get("title", "")[:60]
                        steps.append(f"     • {title}")

                    if len(results) > 3:
                        steps.append(
                            f"     • ... and {len(results) - 3} more"
                        )

                else:
                    steps.append(
                        "   ↳ No results returned for this query"
                    )

            except Exception as e:
                logger.warning(
                    f"Tavily search failed for '{question}': {e}"
                )

                steps.append(
                    f"   ↳ Search failed: {str(e)[:80]}"
                )

        steps.append(
            f"Web search complete — {len(all_results)} URL(s) collected"
        )

        return {
            "web_results": all_results,
            "thinking_steps": steps,
        }

    # ── Node 5: Knowledge base search ───────────────────────────────────────

    def kb_search(state: ResearchState) -> dict:
        qdrant_url = os.getenv("QDRANT_URL", "")

        if not qdrant_url:
            return {
                "vector_results": [],
                "thinking_steps": [
                    "Knowledge base: not configured, "
                    "skipping local search"
                ],
            }

        topic = state["topic"]

        steps = [
            "Searching local knowledge base (Qdrant)..."
        ]

        try:

            from langchain_huggingface import HuggingFaceEmbeddings
            from qdrant_client import QdrantClient

            qdrant_api_key = os.getenv(
                "QDRANT_API_KEY",
                "",
            )

            collection_name = os.getenv(
                "QDRANT_COLLECTION",
                "rag_uploads",
            )

            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )

            steps.append(
                f'Embedding query for vector search: "{topic[:60]}"'
            )

            query_vector = embeddings.embed_query(topic)

            client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
            )

            results = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=3,
                with_payload=True,
                with_vectors=False,
            )

            chunks = []

            for point in results.points:

                chunk_text = point.payload.get(
                    "chunk_text",
                    "",
                )

                if chunk_text:
                    chunks.append(chunk_text)

            steps.append(
                f"✓ Found {len(chunks)} relevant chunk(s) "
                "from knowledge base"
            )

            return {
                "vector_results": chunks,
                "thinking_steps": steps,
            }

        except ImportError:

            steps.append(
                "Knowledge base packages not installed, skipping"
            )

            return {
                "vector_results": [],
                "thinking_steps": steps,
            }

        except Exception as e:

            logger.warning(
                f"KB search failed: {e}"
            )

            steps.append(
                f"Knowledge base search failed: {str(e)[:80]}"
            )

            return {
                "vector_results": [],
                "thinking_steps": steps,
            }

    # ── Node 6: Synthesize ───────────────────────────────────────────────────

    def synthesize(state: ResearchState) -> dict:

        topic = state["topic"]

        web_results = state.get(
            "web_results",
            [],
        )

        vector_results = state.get(
            "vector_results",
            [],
        )

        steps = [
            f"Combining {len(web_results)} web source(s) + "
            f"{len(vector_results)} KB chunk(s)",
            "Drafting report structure: Executive Summary → "
            "Background → Findings → Analysis → Conclusion",
        ]

        context_parts = []

        sources = []

        for result in web_results:

            content = result.get(
                "content",
                "",
            )[:600]

            url = result.get(
                "url",
                "",
            )

            title = result.get(
                "title",
                url,
            )

            if content:

                context_parts.append(
                    f"[Web Source: {title}]\n{content}"
                )

            if url:

                sources.append(
                    {
                        "title": title,
                        "url": url,
                        "content_preview": (
                            content[:120] + "..."
                            if len(content) > 120
                            else content
                        ),
                    }
                )

        for chunk in vector_results:

            context_parts.append(
                f"[Knowledge Base]\n{chunk}"
            )

        context = (
            "\n\n---\n\n".join(context_parts)
            if context_parts
            else "No external sources found."
        )

        source_list = (
            "\n".join(
                f"{i + 1}. {s['title']}\n   {s['url']}"
                for i, s in enumerate(sources)
            )
            if sources
            else "No web sources were found."
        )

        steps.append(
            "Sending context to Hugging Face LLM for synthesis..."
        )

        report_prompt = ChatPromptTemplate.from_template(
            """You are an expert research analyst.

Write a comprehensive, structured research report.

Topic:
{topic}

Research findings:
{context}

Sources:
{source_list}

Use this EXACT structure:

# {topic}

## Executive Summary
Write 2-3 sentences.

## Background & Context
Write 3-5 sentences.

## Current State & Key Findings
Write 3-5 sentences.

## Analysis & Implications
Write 3-5 sentences.

## Conclusion
Write 2-3 sentences.

## Sources
{source_list}

Requirements:

- Use only information supported by the provided research findings.
- Do not invent facts.
- Be specific.
- Use professional analytical language.
- Reference source titles when discussing facts.
- If sources are unavailable, clearly state that the report is based on
  the available research context.
"""
        )

        chain = (
            report_prompt
            | llm
            | StrOutputParser()
        )

        try:

            report = chain.invoke(
                {
                    "topic": topic,
                    "context": context,
                    "source_list": source_list,
                }
            )

        except Exception as e:

            logger.error(
                f"Report generation failed: {e}",
                exc_info=True,
            )

            raise

        steps.append(
            "✓ Report generation complete"
        )

        return {
            "report": report,
            "sources": sources,
            "thinking_steps": steps,
        }

    # ── Routing ──────────────────────────────────────────────────────────────

    def route_after_validation(
        state: ResearchState,
    ) -> str:

        if state.get(
            "is_valid",
            False,
        ):
            return "analyze_query"

        return "__end__"

    def route_search(
        state: ResearchState,
    ) -> str:

        return "web_search"

    # ── Build graph ──────────────────────────────────────────────────────────

    workflow = StateGraph(
        ResearchState
    )

    workflow.add_node(
        "validate_topic",
        validate_topic,
    )

    workflow.add_node(
        "analyze_query",
        analyze_query,
    )

    workflow.add_node(
        "decide_search_strategy",
        decide_search_strategy,
    )

    workflow.add_node(
        "web_search",
        web_search,
    )

    workflow.add_node(
        "kb_search",
        kb_search,
    )

    workflow.add_node(
        "synthesize",
        synthesize,
    )

    workflow.set_entry_point(
        "validate_topic"
    )

    workflow.add_conditional_edges(
        "validate_topic",
        route_after_validation,
        {
            "analyze_query": "analyze_query",
            "__end__": END,
        },
    )

    workflow.add_edge(
        "analyze_query",
        "decide_search_strategy",
    )

    workflow.add_conditional_edges(
        "decide_search_strategy",
        route_search,
        {
            "web_search": "web_search",
        },
    )

    workflow.add_edge(
        "web_search",
        "kb_search",
    )

    workflow.add_edge(
        "kb_search",
        "synthesize",
    )

    workflow.add_edge(
        "synthesize",
        END,
    )

    return workflow.compile()
