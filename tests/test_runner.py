"""Tests for orchestrator.runner — zero-token cost-zeroing guard."""
from unittest.mock import patch

from orchestrator.runner import parse_cli_result, record_cli_run


def test_zero_tokens_forces_cost_to_zero():
    """When both input_tokens and output_tokens are 0, cost_usd must be zeroed
    regardless of the total_cost_usd field in the payload."""
    payload = {
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "total_cost_usd": 1.75,
    }
    assert parse_cli_result(payload) == 0.0


# ---------------------------------------------------------------------------
# Step 5 — comprehensive zero-token cost tests (the test IS the deliverable)
# ---------------------------------------------------------------------------

def test_nonzero_tokens_preserves_cost():
    """When tokens are non-zero, the reported total_cost_usd must pass through unchanged."""
    payload = {
        "usage": {"input_tokens": 100, "output_tokens": 50},
        "total_cost_usd": 0.85,
    }
    assert parse_cli_result(payload) == 0.85


def test_only_input_tokens_zero_does_not_zero_cost():
    """Cost is only zeroed when BOTH token counts are 0; partial zero must not trigger it."""
    payload = {
        "usage": {"input_tokens": 0, "output_tokens": 5},
        "total_cost_usd": 1.23,
    }
    assert parse_cli_result(payload) == 1.23


def test_only_output_tokens_zero_does_not_zero_cost():
    """Cost is only zeroed when BOTH token counts are 0; partial zero must not trigger it."""
    payload = {
        "usage": {"input_tokens": 10, "output_tokens": 0},
        "total_cost_usd": 0.50,
    }
    assert parse_cli_result(payload) == 0.50


def test_missing_usage_key_treated_as_zero_tokens():
    """A payload with no 'usage' key is treated as zero tokens → cost zeroed."""
    payload = {"total_cost_usd": 2.00}
    assert parse_cli_result(payload) == 0.0


def test_zero_tokens_with_zero_cost_stays_zero():
    """Zero tokens with already-zero total_cost_usd must remain 0.0."""
    payload = {
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "total_cost_usd": 0.0,
    }
    assert parse_cli_result(payload) == 0.0


def test_record_cli_run_passes_zeroed_cost_to_record_run():
    """record_cli_run must forward cost_usd=0.0 to record_run when tokens are zero."""
    payload = {
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "total_cost_usd": 1.75,
    }
    with patch("orchestrator.runner.record_run") as mock_record:
        conn = object()  # sentinel — not actually used since record_run is mocked
        record_cli_run(conn, issue_id=42, role="coder", started_at="2024-01-01T00:00:00", payload=payload)

    mock_record.assert_called_once_with(conn, 42, "coder", "2024-01-01T00:00:00", 0.0)
