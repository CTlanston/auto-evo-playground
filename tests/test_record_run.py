"""Tests for src.utils.record_run — double-write guard."""
from src.utils import record_run


# ---------------------------------------------------------------------------
# Step 1 – Double-write prevention
# ---------------------------------------------------------------------------

def test_double_write_is_prevented():
    """Calling record_run twice with same run_id appends only once; second call returns False."""
    storage = []
    run = {"run_id": "abc-123", "tokens": 100, "cost_usd": 0.05}
    first = record_run(storage, run)
    second = record_run(storage, run)
    assert first is True
    assert second is False
    assert len(storage) == 1


def test_different_run_ids_both_recorded():
    """Two distinct run_ids are both stored independently."""
    storage = []
    run1 = {"run_id": "run-1", "tokens": 50, "cost_usd": 0.02}
    run2 = {"run_id": "run-2", "tokens": 60, "cost_usd": 0.03}
    record_run(storage, run1)
    record_run(storage, run2)
    assert len(storage) == 2


def test_no_run_id_always_appended():
    """Runs without run_id cannot be deduplicated; both calls succeed."""
    storage = []
    run = {"tokens": 10, "cost_usd": 0.01}
    r1 = record_run(storage, run)
    r2 = record_run(storage, run)
    assert r1 is True
    assert r2 is True
    assert len(storage) == 2


# ---------------------------------------------------------------------------
# Step 2 – Zero-token phantom cost fix
# ---------------------------------------------------------------------------

def test_zero_token_run_has_zero_cost():
    """A run with tokens=0 must be stored with cost_usd forced to 0.0, not the caller's value."""
    storage = []
    run = {"run_id": "zero-tok", "tokens": 0, "cost_usd": 1.5}
    result = record_run(storage, run)
    assert result is True
    assert storage[0]["cost_usd"] == 0.0
    assert storage[0]["tokens"] == 0
