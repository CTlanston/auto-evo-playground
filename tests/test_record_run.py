"""Tests for src.run_recorder — TDD implementation of record_run fixes."""
import pytest
from src.run_recorder import _store, clear_store, record_run


@pytest.fixture(autouse=True)
def reset_store():
    clear_store()
    yield
    clear_store()


# ---------------------------------------------------------------------------
# Step 1 – single-write: one call must create exactly one store entry
# ---------------------------------------------------------------------------

def test_src_package_exposes_record_run():
    """record_run must be importable directly from the src package."""
    from src import record_run as _pkg
    assert callable(_pkg)
    assert _pkg is record_run


def test_single_call_creates_one_entry():
    """One call to record_run must create exactly one entry in the store."""
    record_run("run-001", 100, 200)
    assert len(_store) == 1
    assert "run-001" in _store


# ---------------------------------------------------------------------------
# Step 2 – idempotency: same run_id twice must not change stored data
# ---------------------------------------------------------------------------

def test_duplicate_run_id_is_ignored():
    """Second call with the same run_id must not overwrite the first entry."""
    record_run("run-002", 100, 200)
    record_run("run-002", 999, 888)
    assert len(_store) == 1
    assert _store["run-002"]["input_tokens"] == 100
    assert _store["run-002"]["output_tokens"] == 200


def test_duplicate_call_returns_original_entry():
    """Second call must return the already-stored entry, not a new object."""
    first = record_run("run-002b", 10, 20)
    second = record_run("run-002b", 99, 99)
    assert second is first


# ---------------------------------------------------------------------------
# Step 3 – zero-token cost: 0 input + 0 output must yield cost == 0
# ---------------------------------------------------------------------------

def test_zero_tokens_have_zero_cost():
    """When both token counts are 0, computed cost must equal 0."""
    entry = record_run("run-003", 0, 0)
    assert entry["cost"] == 0


def test_nonzero_tokens_have_positive_cost():
    """Non-zero tokens must produce a positive cost stored in the entry."""
    entry = record_run("run-003b", 1000, 500)
    assert entry["cost"] > 0


# ---------------------------------------------------------------------------
# Step 4 – None-cost boundary: None tokens must persist as None, no TypeError
# ---------------------------------------------------------------------------

def test_none_input_tokens_stores_none_cost():
    """None input_tokens must not raise TypeError; cost persisted as None."""
    entry = record_run("run-004a", None, 200)
    assert entry["cost"] is None


def test_none_output_tokens_stores_none_cost():
    """None output_tokens must not raise TypeError; cost persisted as None."""
    entry = record_run("run-004b", 100, None)
    assert entry["cost"] is None


def test_both_none_tokens_stores_none_cost():
    """Both token counts None must not raise TypeError; cost persisted as None."""
    entry = record_run("run-004c", None, None)
    assert entry["cost"] is None
