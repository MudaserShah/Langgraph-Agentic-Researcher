"""
config.py — Application settings using Pydantic Settings.

NEW CONCEPT: Pydantic Settings
  In Lecture 18/19 we used os.getenv("OPENAI_API_KEY") scattered throughout the code.
  Pydantic Settings gives us ONE place to define all settings:
    - It reads from the .env file automatically
    - It validates that required values (like API keys) are actually present
    - It provides type hints so we know what type each setting is

  Instead of os.getenv("OPENAI_API_KEY") everywhere, we use:
    from app.config import settings
    key = settings.openai_api_key   ← type-checked, validated, single source of truth

  This follows the same pattern as Lecture 18's config.py.

USAGE:
  from app.config import settings
  print(settings.openai_api_key)
  print(settings.llm_model)
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configurable values for the Agentic Research Assistant.
    Pydantic reads these from environment variables or the .env file.

    Fields without a default value (e.g. openai_api_key) are REQUIRED.
    The server will refuse to start if they are missing.

    Fields with a default value (e.g. tavily_api_key: str = "") are optional.
    """

    # ── Required API keys ─────────────────────────────────────────────────────
    openai_api_key: str
    # No default → server crashes at startup if missing. Intentional: fail fast
    # rather than letting users run research that will fail later.

    # ── Optional API keys ─────────────────────────────────────────────────────
    tavily_api_key: str = ""
    # Empty string = not configured. The web_search node checks for this
    # and logs a warning at startup.

    qdrant_url: str = ""
    # Empty string = no knowledge base. The kb_search node skips gracefully.

    qdrant_api_key: str = ""
    qdrant_collection: str = "rag_uploads"

    # ── LLM settings ─────────────────────────────────────────────────────────
    llm_model: str = "gpt-4o-mini"
    # gpt-4o-mini is the recommended model: fast, affordable, capable enough
    # for research tasks. Students can change this to "gpt-4o" for better quality.

    # ── Database settings ─────────────────────────────────────────────────────
    db_path: str = "research_history.db"
    # Relative path — resolves to backend/research_history.db when uvicorn
    # is launched from the backend/ directory.

    # ── Server settings ───────────────────────────────────────────────────────
    port: int = 8002

    # ── Pydantic config ───────────────────────────────────────────────────────
    model_config = {
        "env_file": ".env",            # Read from .env file in the working directory
        "env_file_encoding": "utf-8",
        "extra": "ignore",             # Ignore extra env vars we don't know about
    }


# Module-level singleton — import this in other files
# "Singleton" means: one instance shared by the whole application.
# Python's import system ensures this is only created once.
settings = Settings()
