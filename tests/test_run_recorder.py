"""Tests for src.run_recorder.record_run — TDD cycles for double-write + phantom-cost fixes."""
from unittest.mock import MagicMock

from src.run_recorder import record_run


def test_record_run_insert_called_exactly_once():
    """record_run must call store.insert exactly once — guards against double-write regression."""
    store = MagicMock()
    record_run({"id": "x", "tokens": 10}, store)
    assert store.insert.call_count == 1


def test_record_run_integration_single_record():
    """One call to record_run must produce exactly one run record in the store."""
    from src.run_recorder import RunStore
    store = RunStore()
    record_run({"id": "run-1", "tokens": 5}, store)
    assert len(store.runs) == 1


def test_record_run_missing_tokens_no_cost_entry():
    """When 'tokens' key is absent, record_run must not write any cost entry."""
    from src.run_recorder import RunStore
    store = RunStore()
    record_run({"id": "run-2"}, store)
    assert len(store.costs) == 0
