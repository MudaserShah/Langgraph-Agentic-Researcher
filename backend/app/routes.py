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
router = APIRouter()
router.add_api_route(
    "/research",
    research,
    methods=["POST"],
    tags=["Agent"],
    summary="Start a streaming research session",
    description="Accepts a research topic and streams SSE events as the agent works.",
)
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

router.add_api_route(
    "/health",
    health,
    methods=["GET"],
    tags=["Ops"],
    summary="Health check — verify the server is running",
)
