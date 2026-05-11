"""Tests for src.run_recorder.record_run — TDD cycles for double-write + phantom-cost fixes."""
from unittest.mock import MagicMock

from src.run_recorder import record_run


def test_record_run_insert_called_exactly_once():
    """record_run must call store.insert exactly once — guards against double-write regression."""
    store = MagicMock()
    record_run({"id": "x", "tokens": 10}, store)
    assert store.insert.call_count == 1
