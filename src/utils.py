"""Utility helpers — auto-edited by Claude agents."""


def record_run(storage, run):
    """Append *run* to *storage*, skipping duplicates by run_id.

    Returns True when the run is stored, False when a duplicate run_id is detected.
    Runs without a run_id key are always appended (cannot be deduplicated).
    """
    run_id = run.get("run_id")
    if run_id is not None and any(r.get("run_id") == run_id for r in storage):
        return False
    if run.get("tokens", 0) == 0:
        run = {**run, "cost_usd": 0.0}
    storage.append(run)
    return True
