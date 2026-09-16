
"""
main.py — Entry point for the Agentic Research Assistant API.

ARCHITECTURE:
  main.py       → FastAPI app + startup/shutdown
  routes.py     → URL route declarations
  api.py        → Endpoint implementations
  agent.py      → LangGraph research agent
  database.py   → SQLite history
  pdf_generator.py → PDF report generation

LLM STACK:
  - Hugging Face LLM
  - Hugging Face/local embeddings
  - Tavily web search
  - Qdrant Cloud knowledge base
  - LangGraph orchestration
  - SQLite report history
  - SSE real-time progress streaming

HOW TO RUN:

    cd lecture_20_agentic_researcher/backend

    uvicorn main:app --reload --port 8002

Frontend:

    cd lecture_20_agentic_researcher/frontend

    npm install
    npm run dev

Frontend:
    http://localhost:5173

Backend:
    http://localhost:8002

API Docs:
    http://localhost:8002/docs
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ─────────────────────────────────────────────────────────────────────────────
# Load environment variables BEFORE importing app.config.
#
# This is important because settings may read environment variables when
# app.config is imported.
# ─────────────────────────────────────────────────────────────────────────────

load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# Application imports
# ─────────────────────────────────────────────────────────────────────────────

from app.agent import build_agent
from app.api import app_state
from app.config import settings
from app.database import init_db
from app.routes import router


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────────────────────
#
# Startup:
#   1. Validate environment configuration
#   2. Initialize SQLite
#   3. Build LangGraph agent
#   4. Store compiled agent in app_state
#
# Shutdown:
#   1. Clear shared application state
#
# The agent is built ONCE at startup and reused for every request.
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):

    # ══════════════════════════════════════════════════════════════════════════
    # STARTUP
    # ══════════════════════════════════════════════════════════════════════════

    logger.info("Starting Agentic Research Assistant...")

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Validate Hugging Face configuration
    # ─────────────────────────────────────────────────────────────────────────
    #
    # We no longer require OPENAI_API_KEY.
    #
    # agent.py uses Hugging Face:
    #
    #     build_agent(hf_token=...)
    #
    # HF_TOKEN comes from .env:
    #
    #     HF_TOKEN=...
    # ─────────────────────────────────────────────────────────────────────────

    if not settings.hf_token:
        raise RuntimeError(
            "HF_TOKEN environment variable is required. "
            "Add your Hugging Face token to .env"
        )

    logger.info("✓ Hugging Face token configured")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Check Tavily configuration
    # ─────────────────────────────────────────────────────────────────────────

    if not settings.tavily_api_key:
        logger.warning(
            "TAVILY_API_KEY not set — "
            "web search will be skipped at runtime"
        )
    else:
        logger.info("✓ Tavily API key configured")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Check Qdrant configuration
    # ─────────────────────────────────────────────────────────────────────────

    if not settings.qdrant_url:
        logger.warning(
            "QDRANT_URL not set — "
            "knowledge base search will be skipped"
        )
    else:
        logger.info("✓ Qdrant configured")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Initialize SQLite database
    # ─────────────────────────────────────────────────────────────────────────
    #
    # Creates the database/table if they don't already exist.
    # ─────────────────────────────────────────────────────────────────────────

    logger.info("Initializing SQLite database...")

    try:
        init_db()
        logger.info("✓ SQLite database ready")
    except Exception as e:
        logger.error(
            f"Database initialization failed: {e}",
            exc_info=True,
        )
        raise

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Build LangGraph research agent
    # ─────────────────────────────────────────────────────────────────────────
    #
    # IMPORTANT:
    #
    # We build the agent ONCE.
    #
    # We do NOT build it inside every /research request.
    #
    # This keeps startup/request architecture clean and avoids repeatedly
    # creating the Hugging Face LLM configuration.
    # ─────────────────────────────────────────────────────────────────────────

    logger.info("Building research agent...")

    try:
        app_state["agent"] = build_agent(
            hf_token=settings.hf_token
        )

        logger.info("✓ Research agent ready")

    except Exception as e:
        logger.error(
            f"Failed to build research agent: {e}",
            exc_info=True,
        )
        raise

    # ─────────────────────────────────────────────────────────────────────────
    # Startup complete
    # ─────────────────────────────────────────────────────────────────────────

    logger.info(
        "Agentic Research Assistant is ready."
    )

    logger.info(
        f"Server: http://localhost:{settings.port}"
    )

    logger.info(
        f"API Docs: http://localhost:{settings.port}/docs"
    )

    yield

    # ══════════════════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ══════════════════════════════════════════════════════════════════════════

    logger.info("Shutting down Agentic Research Assistant...")

    # Clear compiled agent and other shared state.
    app_state.clear()

    logger.info("✓ Application state cleared")
    logger.info("Server shut down.")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI application
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agentic Research Assistant",
    description=(
        "An agentic research system powered by Hugging Face, LangGraph, "
        "Tavily, Qdrant, and SQLite. "
        "The agent validates a research topic, creates a research plan, "
        "searches the web, optionally searches a local knowledge base, "
        "and generates a structured research report. "
        "Research progress is streamed to the frontend using "
        "Server-Sent Events (SSE)."
    ),
    version="3.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────────────────────
#
# Development:
#
#   Frontend → http://localhost:5173
#   Backend  → http://localhost:8002
#
# The browser treats these as different origins, so CORS is required.
#
# For production, replace ["*"] with your actual frontend domain.
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Register API routes
# ─────────────────────────────────────────────────────────────────────────────
#
# routes.py contains:
#
#   POST   /research
#   GET    /history
#   GET    /history/{id}
#   GET    /history/{id}/pdf
#   DELETE /history/{id}
#   GET    /health
#
# The actual endpoint logic lives in api.py.
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(router)


# ─────────────────────────────────────────────────────────────────────────────
# Development entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )

