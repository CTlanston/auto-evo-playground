"""Utility helpers — auto-edited by Claude agents."""
import logging

logger = logging.getLogger(__name__)

_COST_PER_TOKEN = 1e-6  # USD per token


def record_run(run_id, input_tokens, output_tokens, store):
    """Record a model run into *store* (a dict keyed by run_id).

    Raises ValueError if run_id is None or empty.
    Idempotent: a second call with the same run_id is silently ignored (first write wins).
    Zero-token runs (both counts == 0) are phantom runs and not persisted.
    """
    if not run_id:
        raise ValueError(f"run_id must be non-empty, got {run_id!r}")

    if input_tokens < 0 or output_tokens < 0:
        raise ValueError(
            f"token counts must be non-negative; got input_tokens={input_tokens!r}, output_tokens={output_tokens!r}"
        )

    if run_id in store:
        logger.warning("record_run: duplicate run_id=%r; skipping write (first write wins)", run_id)
        return

    if input_tokens == 0 and output_tokens == 0:
        logger.warning("record_run: run_id=%r has zero tokens; skipping phantom write", run_id)
        return

    cost = (input_tokens + output_tokens) * _COST_PER_TOKEN
    store[run_id] = {
        "run_id": run_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    }
    logger.info("record_run: persisted run_id=%r cost=%.6f", run_id, cost)
