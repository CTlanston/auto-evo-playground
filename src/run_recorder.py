"""Run recorder — stdlib only."""

_store = {}


def clear_store():
    """Reset in-memory store (test helper)."""
    _store.clear()


def record_run(run_id, input_tokens, output_tokens):
    """Store a run entry keyed by run_id and return it. First-write-wins."""
    if run_id in _store:
        return _store[run_id]
    entry = {
        "run_id": run_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    _store[run_id] = entry
    return entry
