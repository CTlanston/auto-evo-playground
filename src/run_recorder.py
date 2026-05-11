"""Run recorder — stdlib only."""
from decimal import Decimal

_PRICE_PER_INPUT_TOKEN = Decimal("0.000003")
_PRICE_PER_OUTPUT_TOKEN = Decimal("0.000015")

_store = {}


def calculate_cost(input_tokens, output_tokens):
    """Return Decimal cost from token counts."""
    return (
        Decimal(input_tokens) * _PRICE_PER_INPUT_TOKEN
        + Decimal(output_tokens) * _PRICE_PER_OUTPUT_TOKEN
    )


def clear_store():
    """Reset in-memory store (test helper)."""
    _store.clear()


def record_run(run_id, input_tokens, output_tokens):
    """Store a run entry keyed by run_id and return it. First-write-wins."""
    if run_id in _store:
        return _store[run_id]
    cost = calculate_cost(input_tokens, output_tokens)
    entry = {
        "run_id": run_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    }
    _store[run_id] = entry
    return entry
