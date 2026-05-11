"""CLI runner utilities for orchestrating agent runs."""
import sqlite3

from orchestrator.db import record_run


def parse_cli_result(payload: dict) -> float:
    """Extract cost_usd from a CLI JSON envelope, zeroing it when no tokens were consumed.

    A zero-token payload means the CLI reported stale cost data from a prior run;
    forcing cost to 0 prevents phantom charges.
    """
    usage = payload.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost_usd = float(payload.get("total_cost_usd", 0.0))

    if input_tokens == 0 and output_tokens == 0:
        cost_usd = 0.0

    return cost_usd


def record_cli_run(
    conn: sqlite3.Connection,
    issue_id: int,
    role: str,
    started_at: str,
    payload: dict,
) -> None:
    """Parse a CLI result payload and record the run, applying the zero-token guard."""
    cost_usd = parse_cli_result(payload)
    record_run(conn, issue_id, role, started_at, cost_usd)
