"""Tests for orchestrator.runner — zero-token cost-zeroing guard."""
from orchestrator.runner import parse_cli_result


def test_zero_tokens_forces_cost_to_zero():
    """When both input_tokens and output_tokens are 0, cost_usd must be zeroed
    regardless of the total_cost_usd field in the payload."""
    payload = {
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "cost_usd": 1.75,
    }
    assert parse_cli_result(payload) == 0.0
