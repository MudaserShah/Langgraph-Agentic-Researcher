"""
routes.py — API route declarations for the Agentic Research Assistant.

WHAT THIS FILE DOES:
  This file only declares WHICH URL maps to WHICH function.
  The actual implementation lives in api.py.

  This mirrors the structure from Lecture 18:
    routes.py  ← "POST /research goes to the research() function"
    api.py     ← "Here is what the research() function does"

WHY SEPARATE THEM?
  When you're reading the code top-down, you first look at routes.py
  to understand the API surface (what endpoints exist). Then you dive
  into api.py to understand what each endpoint actually does.
  This makes large APIs much easier to navigate.

HOW TO READ THE ROUTES:
  router.add_api_route(path, handler_function, methods=[...])

  path     — the URL path, e.g. "/research" or "/history/{report_id}"
  handler  — the function imported from api.py that handles this request
  methods  — HTTP methods: POST (create), GET (read), DELETE (delete)
"""

from fastapi import APIRouter

from app.api import (
    delete_history_report,
    download_pdf,
    get_history,
    get_history_report,
    health,
    research,
)
from app.models import DeleteResponse, HistoryListResponse

# APIRouter groups related routes together.
# In main.py we do app.include_router(router) to register all routes at once.
router = APIRouter()

# ── Agent routes ──────────────────────────────────────────────────────────────
router.add_api_route(
    "/research",
    research,
    methods=["POST"],
    tags=["Agent"],
    summary="Start a streaming research session",
    description="Accepts a research topic and streams SSE events as the agent works.",
)

# ── History routes ────────────────────────────────────────────────────────────
router.add_api_route(
    "/history",
    get_history,
    methods=["GET"],
    response_model=HistoryListResponse,
    tags=["History"],
    summary="List all past research reports",
)

router.add_api_route(
    "/history/{report_id}",
    get_history_report,
    methods=["GET"],
    tags=["History"],
    summary="Get a full research report by ID",
)

router.add_api_route(
    "/history/{report_id}/pdf",
    download_pdf,
    methods=["GET"],
    tags=["History"],
    summary="Download a research report as PDF",
)

router.add_api_route(
    "/history/{report_id}",
    delete_history_report,
    methods=["DELETE"],
    response_model=DeleteResponse,
    tags=["History"],
    summary="Delete a research report",
)

# ── Ops routes ────────────────────────────────────────────────────────────────
router.add_api_route(
    "/health",
    health,
    methods=["GET"],
    tags=["Ops"],
    summary="Health check — verify the server is running",
)
