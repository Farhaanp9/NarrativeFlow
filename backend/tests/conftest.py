"""Shared test fixtures."""

import os
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Override DB path and LLM URL before any app imports
_tmp = tempfile.mkdtemp()
_db_path = str(Path(_tmp) / "test.db")
os.environ["NF_DB_PATH"] = _db_path
os.environ["NF_LLM_BASE_URL"] = "http://localhost:99999/v1"

from narrativeflow.api.main import app  # noqa: E402
from narrativeflow.config import Settings, get_settings  # noqa: E402
from narrativeflow.storage.database import init_db  # noqa: E402


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    # Ensure DB is initialized (lifespan doesn't run with ASGITransport)
    await init_db(Path(_db_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
