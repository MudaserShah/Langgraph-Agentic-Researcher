"""
models.py — Pydantic models for the Agentic Research Assistant.

WHAT ARE PYDANTIC MODELS?
  Pydantic models are Python classes that validate data automatically.
  When FastAPI receives a JSON request body, it passes the JSON through
  the matching Pydantic model. If a required field is missing or the
  wrong type, FastAPI returns a clear 422 error — no manual checking needed.

  Same for responses: FastAPI serializes the model to JSON automatically.

TWO KINDS OF MODELS HERE:
  1. HTTP request/response models  — define the shape of API data
  2. (Note: LangGraph state is defined as a TypedDict in agent.py, not here)
"""

from typing import List, Optional

from pydantic import BaseModel


# ── Request models ────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    """
    The body of POST /research.
    The user sends a topic; optionally forces web search on/off.
    """

    topic: str
    # None = let the agent decide the search strategy
    # True = always do web search (override agent's choice)
    use_web_search: Optional[bool] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"topic": "Impact of large language models on education"},
                {"topic": "Latest advances in quantum computing 2025", "use_web_search": True},
            ]
        }
    }


# ── Response models ───────────────────────────────────────────────────────────

class Source(BaseModel):
    """A single web source found during research."""
    title: str
    url: str
    content_preview: str   # First ~120 characters of the page content


class ResearchReport(BaseModel):
    """
    Returned by GET /history/{id}.
    Contains the full report text and all metadata.
    """
    topic: str
    report_md: str           # Full markdown report text
    sources: List[Source]
    search_strategy: str     # "web_only" or "both"
    sub_questions: List[str] # The 3 sub-questions the agent generated
    url_count: int
    created_at: str


# ── History models (NEW in Lecture 19) ───────────────────────────────────────

class HistoryItem(BaseModel):
    """
    A summary row shown in the history list.

    We deliberately do NOT include the full report text here —
    it can be large. The history list only shows enough info to
    identify and choose a report. Full text is fetched on demand.
    """
    id: str            # Short 8-character ID used in /history/{id} URLs
    topic: str
    url_count: int     # How many web URLs were found during research
    created_at: str    # ISO timestamp: "2025-04-14T16:30:00"


class HistoryListResponse(BaseModel):
    """Returned by GET /history."""
    reports: List[HistoryItem]
    total: int          # Total count (same as len(reports) for now, useful if we add pagination)


class DeleteResponse(BaseModel):
    """Returned by DELETE /history/{id}."""
    status: str    # "deleted"
    id: str
