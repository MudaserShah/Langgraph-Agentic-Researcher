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

    hf_token: str = ""

    tavily_api_key: str = ""

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "rag_uploads"
    llm_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    embedding_provider: str = "huggingface"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    db_path: str = "research_history.db"

    port: int = 8002

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Module-level singleton
settings = Settings()