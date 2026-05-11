"""SQLite helpers for recording agent runs."""
import sqlite3

_UNIQUE_INDEX = "uq_runs_issue_role_started"

_SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS runs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id    INTEGER NOT NULL,
        role        TEXT    NOT NULL,
        started_at  TEXT    NOT NULL,
        cost_usd    REAL    NOT NULL DEFAULT 0.0
    )
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Create schema and apply migration guards."""
    conn.execute(_SCHEMA_SQL)
    _migrate_unique_index(conn)
    conn.commit()


def _migrate_unique_index(conn: sqlite3.Connection) -> None:
    """Add UNIQUE index on (issue_id, role, started_at) if not already present."""
    existing = {row[1] for row in conn.execute("PRAGMA index_list('runs')").fetchall()}
    if _UNIQUE_INDEX not in existing:
        conn.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS {_UNIQUE_INDEX} "
            "ON runs (issue_id, role, started_at)"
        )


def record_run(
    conn: sqlite3.Connection,
    issue_id: int,
    role: str,
    started_at: str,
    cost_usd: float,
) -> None:
    """Insert a run record into the database."""
    conn.execute(
        "INSERT INTO runs (issue_id, role, started_at, cost_usd) VALUES (?, ?, ?, ?)",
        (issue_id, role, started_at, cost_usd),
    )
    conn.commit()
