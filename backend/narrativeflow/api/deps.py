"""Dependency injection for FastAPI routes."""

from collections.abc import AsyncGenerator
from functools import lru_cache

import aiosqlite

from narrativeflow.config import Settings, get_settings
from narrativeflow.llm.client import LLMClient
from narrativeflow.storage.database import get_connection


@lru_cache
def get_llm_client() -> LLMClient:
    """Return a cached LLM client instance."""
    return LLMClient(get_settings())


async def get_db() -> AsyncGenerator[aiosqlite.Connection]:
    """Yield an async SQLite connection, closing on exit."""
    settings = get_settings()
    db = await get_connection(settings.db_path)
    try:
        yield db
    finally:
        await db.close()


def get_app_settings() -> Settings:
    """Return application settings."""
    return get_settings()
