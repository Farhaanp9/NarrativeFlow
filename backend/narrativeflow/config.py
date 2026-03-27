"""Application configuration via environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """NarrativeFlow application settings."""

    # Database
    db_path: Path = Path("data/narrativeflow.db")

    # LLM
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "llama3.1:8b"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"

    model_config = {"env_prefix": "NF_"}


def get_settings() -> Settings:
    """Return application settings (cached on first call)."""
    return Settings()
