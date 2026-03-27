"""SQLite database initialization and connection management."""

from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS simulations (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'configuring',
    config JSON NOT NULL,
    seed_narrative JSON,
    current_tick INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS archetypes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    simulation_id TEXT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    profile JSON NOT NULL,
    population_pct REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS narratives (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    parent_id TEXT REFERENCES narratives(id),
    content TEXT NOT NULL,
    mutation_type TEXT NOT NULL,
    emotional_charge REAL,
    virality_modifier REAL,
    origin_tick INTEGER,
    origin_archetype_id INTEGER,
    spread_count INTEGER DEFAULT 0,
    lineage JSON
);

CREATE TABLE IF NOT EXISTS tick_metrics (
    simulation_id TEXT NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    tick INTEGER NOT NULL,
    metrics JSON NOT NULL,
    PRIMARY KEY (simulation_id, tick)
);

CREATE TABLE IF NOT EXISTS reports (
    simulation_id TEXT PRIMARY KEY REFERENCES simulations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSON
);

CREATE TABLE IF NOT EXISTS agent_snapshots (
    simulation_id TEXT PRIMARY KEY REFERENCES simulations(id) ON DELETE CASCADE,
    agent_data BLOB NOT NULL
);
"""


async def init_db(db_path: Path) -> None:
    """Create database and all tables. Enables WAL mode for concurrent reads."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript(SCHEMA)
        await db.commit()


async def get_connection(db_path: Path) -> aiosqlite.Connection:
    """Return an async SQLite connection with WAL mode and foreign keys enabled."""
    db = await aiosqlite.connect(db_path)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = aiosqlite.Row
    return db
