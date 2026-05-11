"""Tests for orchestrator.db — migration guard and schema."""
import sqlite3

from orchestrator.db import init_db


def _legacy_conn():
    """In-memory DB with runs table but NO unique index (simulates pre-migration state)."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            started_at TEXT NOT NULL,
            cost_usd REAL NOT NULL DEFAULT 0.0
        )
    """)
    conn.commit()
    return conn


def test_migration_guard_adds_unique_index_to_legacy_db():
    """init_db on a DB without the unique index must add it without raising."""
    conn = _legacy_conn()

    before = {row[1] for row in conn.execute("PRAGMA index_list('runs')").fetchall()}
    assert not any("uq_runs" in name for name in before), "pre-condition: index absent"

    init_db(conn)

    after = {row[1] for row in conn.execute("PRAGMA index_list('runs')").fetchall()}
    assert any("uq_runs" in name for name in after), "unique index must be present after init_db"
