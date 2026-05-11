"""Utility helpers — auto-edited by Claude agents."""

_COST_PER_TOKEN = 1e-6  # USD per token


def record_run(run_id, input_tokens, output_tokens, store):
    """Record a model run into *store* (a dict keyed by run_id).

    Idempotent: a second call with the same run_id is silently ignored.
    """
    if run_id in store:
        return

    cost = (input_tokens + output_tokens) * _COST_PER_TOKEN
    store[run_id] = {
        "run_id": run_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    }
