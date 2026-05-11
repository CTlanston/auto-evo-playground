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
