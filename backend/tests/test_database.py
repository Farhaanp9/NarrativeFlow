"""Tests for database initialization."""

import tempfile
from pathlib import Path

import aiosqlite

from narrativeflow.storage.database import (
    fail_interrupted_simulations,
    get_connection,
    init_db,
)

EXPECTED_TABLES = {
    "simulations",
    "archetypes",
    "narratives",
    "tick_metrics",
    "reports",
    "agent_snapshots",
}


async def test_init_db_creates_all_tables() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        await init_db(db_path)

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = {row[0] for row in await cursor.fetchall()}

    assert tables == EXPECTED_TABLES


async def test_init_db_creates_parent_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "nested" / "deep" / "test.db"
        await init_db(db_path)
        assert db_path.exists()


async def test_wal_mode_enabled() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        await init_db(db_path)

        db = await get_connection(db_path)
        try:
            cursor = await db.execute("PRAGMA journal_mode")
            row = await cursor.fetchone()
            assert row[0] == "wal"
        finally:
            await db.close()


async def test_foreign_keys_enabled() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        await init_db(db_path)

        db = await get_connection(db_path)
        try:
            cursor = await db.execute("PRAGMA foreign_keys")
            row = await cursor.fetchone()
            assert row[0] == 1
        finally:
            await db.close()


async def test_fail_interrupted_simulations() -> None:
    """Runs a previous process left unfinished are marked failed; others stay."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        await init_db(db_path)
        statuses = ["initializing", "running", "paused", "completed", "failed"]
        async with aiosqlite.connect(db_path) as db:
            for i, status in enumerate(statuses):
                await db.execute(
                    "INSERT INTO simulations (id, status, config) VALUES (?, ?, '{}')",
                    (str(i), status),
                )
            await db.commit()

        assert await fail_interrupted_simulations(db_path) == 3

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT status FROM simulations ORDER BY id")
            rows = [r[0] for r in await cursor.fetchall()]
        assert rows == ["failed", "failed", "failed", "completed", "failed"]
