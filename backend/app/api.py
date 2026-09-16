
import asyncio
import json
import logging
import os

from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse

from app.agent import ResearchState, build_agent
from app.config import settings
from app.database import delete_report, get_report, list_reports, save_report
from app.models import DeleteResponse, HistoryItem, HistoryListResponse, ResearchRequest

logger = logging.getLogger(__name__)



app_state: dict = {}



NODE_DISPLAY = {
    "validate_topic":           "Validating research topic",
    "analyze_query":            "Analyzing research topic",
    "decide_search_strategy":   "Planning search strategy",
    "web_search":               "Searching the web",
    "kb_search":                "Searching knowledge base",
    "synthesize":               "Writing research report",
}



def sse_event(data: dict) -> str:
    """
    Format a Python dict as an SSE event string.

    SSE protocol:
      - Each event starts with "data: "
      - Each event ends with TWO newlines (\\n\\n)
      - The browser's ReadableStream reader splits on these \\n\\n boundaries

    Example output:
      'data: {"event": "thinking", "message": "Analyzing..."}\\n\\n'
    """
    return f"data: {json.dumps(data)}\n\n"



async def research(request: ResearchRequest):
    """
    Stream a research report using Server-Sent Events.

    The client sends: {"topic": "AI in healthcare", "use_web_search": true}
    The server keeps the connection open and streams events as the agent works:

      {"event": "start",      "message": "Starting research on: ..."}
      {"event": "node_start", "node": "validate_topic", "display": "Validating..."}
      {"event": "thinking",   "node": "validate_topic", "message": "✓ Valid topic..."}
      {"event": "node_start", "node": "web_search", "display": "Searching the web"}
      {"event": "thinking",   "node": "web_search", "message": "🔍 Query 1/3: ..."}
      ...
      {"event": "complete",   "report": "# ...", "sources": [...], "report_id": "a1b2c3d4"}
      {"event": "summary",    "stats": {...}}
      data: [DONE]

    The frontend reads these events as they arrive and updates the UI in real time.
    """
    if "agent" not in app_state:
        raise HTTPException(status_code=503, detail="Agent not ready — server is still starting up")

    agent = app_state["agent"]

    # Build the initial state for this research session
    # Every field must be present (TypedDict requires this)
    initial_state = ResearchState(
        topic=request.topic,
        override_web_search=request.use_web_search,
        is_valid=False,          # Will be set by validate_topic node
        validation_reason="",
        sub_questions=[],
        search_strategy="",
        web_results=[],
        vector_results=[],
        report="",
        sources=[],
        thinking_steps=[],
    )

    async def event_generator():
        """
        Async generator that yields SSE events as the agent runs.

        We use agent.astream(stream_mode="updates") which yields a dict after
        each node completes with only the state fields that node changed.

        WHY NOT astream_events?
          astream_events(version="v2") forces the LLM into token-streaming mode
          internally, which triggers a pydantic-core bug with structured output
          (by_alias=None cannot be converted to PyBool). astream() avoids that
          code path entirely — it runs each node to completion and returns the
          final output dict, which is all we need.

        Each yielded chunk looks like:
          {"validate_topic": {"is_valid": True, "thinking_steps": [...], ...}}
          {"analyze_query":  {"sub_questions": [...], "thinking_steps": [...], ...}}
          ...
        The thinking_steps in each chunk are ONLY the new steps that node added
        (because of the Annotated[List[str], add] reducer in ResearchState).
        """
        try:
            # Tell the frontend we're starting
            yield sse_event({"event": "start", "message": f"Starting research on: {request.topic}"})

            # These will be populated as we process node outputs
            final_report = ""
            final_sources = []
            final_sub_questions = []
            final_strategy = "web_only"
            final_is_valid = True
            final_validation_reason = ""
            final_vector_results = []

            async for chunk in agent.astream(initial_state, stream_mode="updates"):
                for node_name, output in chunk.items():
                    if node_name not in NODE_DISPLAY:
                        continue  # Skip internal LangGraph bookkeeping nodes

                    yield sse_event({
                        "event": "node_start",
                        "node": node_name,
                        "display": NODE_DISPLAY[node_name],
                        "message": f"{NODE_DISPLAY[node_name]}...",
                    })
                    await asyncio.sleep(0.05)

                    steps = output.get("thinking_steps", [])
                    for step in steps:
                        yield sse_event({
                            "event": "thinking",
                            "node": node_name,
                            "message": step,
                        })
                        await asyncio.sleep(0.08)

                 
                    if node_name == "synthesize":
                        final_report = output.get("report", "")
                        final_sources = output.get("sources", [])

                    if node_name == "analyze_query":
                        final_sub_questions = output.get("sub_questions", [])
                        final_strategy = output.get("search_strategy", "web_only")

                    if node_name == "validate_topic":
                        final_is_valid = output.get("is_valid", True)
                        final_validation_reason = output.get("validation_reason", "")

                    if node_name == "kb_search":
                        final_vector_results = output.get("vector_results", [])


            if not final_is_valid:
                # Topic was rejected by validate_topic node
                yield sse_event({
                    "event": "error",
                    "message": f"Invalid research topic: {final_validation_reason}",
                })

            elif final_report:
                # Success — save the report to SQLite and send the complete event
                report_id = save_report(
                    topic=request.topic,
                    report_md=final_report,
                    sources=final_sources,
                    sub_questions=final_sub_questions,
                )
                logger.info(f"Report saved with id={report_id}")


                yield sse_event({
                    "event": "complete",
                    "report": final_report,
                    "sources": final_sources,
                    "sub_questions": final_sub_questions,
                    "report_id": report_id,   # Frontend uses this for PDF download
                })

          
                yield sse_event({
                    "event": "summary",
                    "stats": {
                        "topic": request.topic,
                        "sub_questions": final_sub_questions,
                        "urls_searched": len(final_sources),
                        "kb_searched": bool(final_vector_results),
                        "strategy": final_strategy,
                    },
                })

            else:
                # Something went wrong but no exception was raised
                yield sse_event({
                    "event": "error",
                    "message": "Report generation failed — agent produced no output",
                })

        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            yield sse_event({"event": "error", "message": str(e)})

        finally:
            # [DONE] sentinel tells the frontend the stream is finished
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",       # Don't cache streaming responses
            "Connection": "keep-alive",
           
            "X-Accel-Buffering": "no",
        },
    )



def get_history():
    """
    Return a list of all past research reports, newest first.

    Returns only summary information (id, topic, url_count, created_at).
    Use GET /history/{id} to get the full report text.
    """
    reports = list_reports()  # From database.py
    return HistoryListResponse(
        reports=[HistoryItem(**r) for r in reports],
        total=len(reports),
    )


def get_history_report(report_id: str):
    """
    Return the full details of one past research report.

    Called when the user clicks "View" on a history item in the frontend.
    Returns: {id, topic, report_md, sources, sub_questions, url_count, created_at}
    """
    report = get_report(report_id)   # From database.py
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return report


def download_pdf(report_id: str):
    """
    Generate and return a PDF version of a past research report.

    HOW IT WORKS:
      1. Fetch the report from SQLite
      2. Convert markdown → PDF bytes using reportlab (pdf_generator.py)
      3. Return as a file download (application/pdf)

    The browser receives this as a file download prompt, just like downloading
    any file from a website.

    Content-Disposition: attachment tells the browser to save the file
    instead of trying to display it inline.
    """
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

    # Import here to keep startup fast if reportlab is not installed
    from app.pdf_generator import generate_pdf

    try:
        pdf_bytes = generate_pdf(
            topic=report["topic"],
            report_md=report["report_md"],
            sources=report["sources"],
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # Sanitize the topic for use in the filename (remove characters invalid in filenames)
    safe_topic = "".join(c if c.isalnum() or c in " _-" else "_" for c in report["topic"])
    safe_topic = safe_topic[:40].strip()  # Max 40 chars to keep filename readable
    filename = f"research_{safe_topic}_{report_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            # "attachment" = save as file download (not open in browser tab)
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def delete_history_report(report_id: str):
    """
    Delete a past research report from history.

    Returns 404 if the report_id does not exist.
    Returns {"status": "deleted", "id": "..."} on success.
    """
    deleted = delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return DeleteResponse(status="deleted", id=report_id)


def health():
    """
    Quick status check. Useful for verifying the server is running before
    testing the frontend.
    """
    return {
        "status": "ok",
        "agent_ready": "agent" in app_state,
        "qdrant_configured": bool(settings.qdrant_url),
    }
