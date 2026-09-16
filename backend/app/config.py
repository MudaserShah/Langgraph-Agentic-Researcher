"""
config.py — Application settings using Pydantic Settings.

Centralized configuration for the Agentic Research Assistant.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configurable values for the Agentic Research Assistant.

    Pydantic reads these values from environment variables or .env.
    """

    # ── Hugging Face ──────────────────────────────────────────────────────────
    hf_token: str = ""

    # ── Optional API keys ─────────────────────────────────────────────────────
    tavily_api_key: str = ""

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "rag_uploads"

    # ── LLM settings ─────────────────────────────────────────────────────────
    llm_model: str = "meta-llama/Llama-3.1-8B-Instruct"

    # ── Embedding settings ────────────────────────────────────────────────────
    embedding_provider: str = "huggingface"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Database settings ─────────────────────────────────────────────────────
    db_path: str = "research_history.db"

    # ── Server settings ───────────────────────────────────────────────────────
    port: int = 8002

    # ── Pydantic config ───────────────────────────────────────────────────────
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Module-level singleton
settings = Settings()