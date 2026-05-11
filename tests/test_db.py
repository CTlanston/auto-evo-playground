"""Tests for orchestrator.db — migration guard and schema."""
import sqlite3

from orchestrator.db import init_db, record_run


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


def _fresh_conn():
    """In-memory DB fully initialised via init_db."""
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def test_migration_guard_adds_unique_index_to_legacy_db():
    """init_db on a DB without the unique index must add it without raising."""
    conn = _legacy_conn()

    before = {row[1] for row in conn.execute("PRAGMA index_list('runs')").fetchall()}
    assert not any("uq_runs" in name for name in before), "pre-condition: index absent"

    init_db(conn)

    after = {row[1] for row in conn.execute("PRAGMA index_list('runs')").fetchall()}
    assert any("uq_runs" in name for name in after), "unique index must be present after init_db"


def test_record_run_duplicate_key_produces_single_row():
    """Calling record_run twice with the same (issue_id, role, started_at) must not raise
    and must leave exactly one row in the database."""
    conn = _fresh_conn()

    record_run(conn, issue_id=1, role="coder", started_at="2024-01-01T00:00:00", cost_usd=0.5)
    record_run(conn, issue_id=1, role="coder", started_at="2024-01-01T00:00:00", cost_usd=0.9)

    count = conn.execute(
        "SELECT COUNT(*) FROM runs WHERE issue_id=1 AND role='coder' AND started_at='2024-01-01T00:00:00'"
    ).fetchone()[0]
    assert count == 1, f"expected exactly 1 row, got {count}"


# ---------------------------------------------------------------------------
# Step 4 — comprehensive idempotent-INSERT tests (the test IS the deliverable)
# ---------------------------------------------------------------------------

def test_record_run_idempotent_preserves_first_write():
    """The first call's cost_usd must be retained; the second call must not overwrite it."""
    conn = _fresh_conn()

    record_run(conn, issue_id=7, role="reviewer", started_at="2024-06-01T12:00:00", cost_usd=0.42)
    record_run(conn, issue_id=7, role="reviewer", started_at="2024-06-01T12:00:00", cost_usd=9.99)

    row = conn.execute(
        "SELECT cost_usd FROM runs WHERE issue_id=7 AND role='reviewer'"
    ).fetchone()
    assert row is not None
    assert row[0] == 0.42, "second call must not overwrite the first write"


def test_record_run_different_role_same_issue_creates_separate_rows():
    """Different roles with the same issue_id and started_at are distinct keys → two rows."""
    conn = _fresh_conn()

    record_run(conn, issue_id=2, role="coder", started_at="2024-01-01T00:00:00", cost_usd=0.1)
    record_run(conn, issue_id=2, role="reviewer", started_at="2024-01-01T00:00:00", cost_usd=0.2)

    count = conn.execute(
        "SELECT COUNT(*) FROM runs WHERE issue_id=2"
    ).fetchone()[0]
    assert count == 2, "different roles must produce separate rows"


def test_record_run_different_started_at_creates_separate_rows():
    """Same issue_id and role but different started_at is a distinct key → two rows."""
    conn = _fresh_conn()

    record_run(conn, issue_id=3, role="coder", started_at="2024-01-01T00:00:00", cost_usd=0.1)
    record_run(conn, issue_id=3, role="coder", started_at="2024-01-02T00:00:00", cost_usd=0.2)

    count = conn.execute(
        "SELECT COUNT(*) FROM runs WHERE issue_id=3 AND role='coder'"
    ).fetchone()[0]
    assert count == 2, "different started_at must produce separate rows"


def test_record_run_many_duplicates_stays_one_row():
    """Ten duplicate calls must still result in exactly one stored row."""
    conn = _fresh_conn()

    for _ in range(10):
        record_run(conn, issue_id=99, role="planner", started_at="2025-01-01T00:00:00", cost_usd=1.0)

    count = conn.execute("SELECT COUNT(*) FROM runs WHERE issue_id=99").fetchone()[0]
    assert count == 1
