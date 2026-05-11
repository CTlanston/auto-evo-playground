"""Tests for src.utils.record_run."""
import logging
import pytest
from unittest.mock import patch

from src.utils import record_run


# ---------------------------------------------------------------------------
# Step 1 – Single-write: one call produces exactly one record
# ---------------------------------------------------------------------------

def test_single_call_produces_one_record():
    """Calling record_run once must write exactly one entry to the store."""
    store = {}
    record_run("run-abc", 10, 5, store)
    assert len(store) == 1
    assert "run-abc" in store


def test_single_record_contains_expected_fields():
    """The stored record must contain run_id, input_tokens, output_tokens, cost."""
    store = {}
    record_run("run-001", 100, 50, store)
    record = store["run-001"]
    assert record["run_id"] == "run-001"
    assert record["input_tokens"] == 100
    assert record["output_tokens"] == 50
    assert "cost" in record


# ---------------------------------------------------------------------------
# Step 2 – Double-write: idempotency guard
# ---------------------------------------------------------------------------

def test_double_call_same_run_id_produces_one_record():
    """Calling record_run twice with the same run_id must leave only one record."""
    store = {}
    record_run("run-dup", 10, 5, store)
    record_run("run-dup", 10, 5, store)
    assert len(store) == 1


def test_double_call_does_not_overwrite_first_record():
    """Second call with same run_id must not overwrite the first record's data."""
    store = {}
    record_run("run-dup2", 100, 50, store)
    original = dict(store["run-dup2"])
    record_run("run-dup2", 999, 999, store)
    assert store["run-dup2"] == original


def test_different_run_ids_both_stored():
    """Two calls with different run_ids must both be stored."""
    store = {}
    record_run("run-A", 10, 5, store)
    record_run("run-B", 20, 10, store)
    assert len(store) == 2
    assert "run-A" in store
    assert "run-B" in store


# ---------------------------------------------------------------------------
# Step 3 – Zero-token phantom cost
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("in_tok,out_tok", [
    (1, 0),
    (0, 1),
    (5, 10),
])
def test_nonzero_tokens_produce_positive_cost(in_tok, out_tok):
    """At least one non-zero token count must produce a positive cost."""
    store = {}
    run_id = f"run-cost-{in_tok}-{out_tok}"
    record_run(run_id, in_tok, out_tok, store)
    assert run_id in store
    assert store[run_id]["cost"] > 0


def test_zero_token_run_is_not_persisted():
    """A zero-token run is a phantom and must NOT be written to the store."""
    store = {}
    record_run("run-zero", 0, 0, store)
    assert "run-zero" not in store


# ---------------------------------------------------------------------------
# Step 4 – run_id validation: None and empty string must be rejected
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_id", [None, ""])
def test_none_or_empty_run_id_raises_value_error(bad_id):
    """record_run must raise ValueError when run_id is None or empty string."""
    store = {}
    with pytest.raises(ValueError):
        record_run(bad_id, 10, 5, store)


@pytest.mark.parametrize("bad_id", [None, ""])
def test_invalid_run_id_does_not_write_to_store(bad_id):
    """Store must be untouched when run_id is invalid."""
    store = {}
    try:
        record_run(bad_id, 10, 5, store)
    except ValueError:
        pass
    assert len(store) == 0
