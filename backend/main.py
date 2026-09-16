import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


from app.agent import build_agent
from app.api import app_state
from app.config import settings
from app.database import init_db
from app.routes import router


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting Agentic Research Assistant...")
    if not settings.hf_token:
        raise RuntimeError(
            "HF_TOKEN environment variable is required. "
            "Add your Hugging Face token to .env"
        )

    logger.info("✓ Hugging Face token configured")

    if not settings.tavily_api_key:
        logger.warning(
            "TAVILY_API_KEY not set — "
            "web search will be skipped at runtime"
        )
    else:
        logger.info("✓ Tavily API key configured")

    if not settings.qdrant_url:
        logger.warning(
            "QDRANT_URL not set — "
            "knowledge base search will be skipped"
        )
    else:
        logger.info("✓ Qdrant configured")

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

    logger.info("Shutting down Agentic Research Assistant...")

    app_state.clear()

    logger.info("✓ Application state cleared")
    logger.info("Server shut down.")


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

app.include_router(router)

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )

