"""Tests for src.run_recorder.record_run — TDD cycles for double-write + phantom-cost fixes."""
import pytest
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


@pytest.mark.parametrize("run_data,expected_cost_count,expected_cost", [
    ({"id": "r1", "tokens": 0}, 1, 0.0),   # tokens=0 is a valid zero: must write cost entry
    ({"id": "r2"},              0, None),    # tokens key absent: must skip cost entry entirely
])
def test_record_run_tokens_boundary(run_data, expected_cost_count, expected_cost):
    """Distinguish tokens=0 (write cost=0) from absent tokens key (skip cost entry)."""
    from src.run_recorder import RunStore
    store = RunStore()
    record_run(run_data, store)
    assert len(store.costs) == expected_cost_count
    if expected_cost is not None:
        assert store.costs[0]["cost"] == expected_cost


def test_record_run_none_tokens_no_cost_entry():
    """tokens=None (common null API response) must be treated as missing — skip cost, no TypeError."""
    from src.run_recorder import RunStore
    store = RunStore()
    record_run({"id": "run-none", "tokens": None}, store)
    assert len(store.costs) == 0


def test_record_run_negative_tokens_no_cost_entry():
    """tokens<0 is illegal dirty data — must skip cost entry, not write negative phantom cost."""
    from src.run_recorder import RunStore
    store = RunStore()
    record_run({"id": "run-neg", "tokens": -5}, store)
    assert len(store.costs) == 0


def test_record_run_missing_id_no_cost_entry():
    """When 'id' key is absent, record_run must not write a phantom run_id=None cost entry."""
    from src.run_recorder import RunStore
    store = RunStore()
    record_run({"tokens": 5}, store)
    assert len(store.costs) == 0


def test_record_run_bool_tokens_no_cost_entry():
    """tokens=True/False (bool subclasses int) must be rejected — same policy as telemetry_aggregator."""
    from src.run_recorder import RunStore
    store = RunStore()
    record_run({"id": "run-bool", "tokens": True}, store)
    assert len(store.costs) == 0


def test_record_run_string_tokens_no_cost_no_typeerror():
    """tokens='abc' (dirty API response) must not raise TypeError and must skip cost entry."""
    from src.run_recorder import RunStore
    store = RunStore()
    record_run({"id": "run-str", "tokens": "abc"}, store)
    assert len(store.costs) == 0


def test_record_run_negative_tokens_emits_warning():
    """tokens<0 is illegal dirty data — must emit a logging.warning (not swallowed silently)."""
    from src.run_recorder import RunStore
    from unittest.mock import patch
    store = RunStore()
    with patch("src.run_recorder.logging") as mock_log:
        record_run({"id": "run-neg-warn", "tokens": -3}, store)
    mock_log.warning.assert_called_once()
    assert len(store.costs) == 0


def test_record_run_insert_cost_mutation_safe():
    """Mutating run_data after record_run must not alter stored run or cost entries."""
    from src.run_recorder import RunStore, COST_PER_TOKEN
    store = RunStore()
    run = {"id": "run-mut", "tokens": 10}
    record_run(run, store)
    expected_cost = 10 * COST_PER_TOKEN

    # Mutate source dict after the call
    run["id"] = "mutated"
    run["tokens"] = 9999

    # Stored run must reflect value at call time (shallow-copied by insert)
    assert store.runs[0]["id"] == "run-mut"
    # Stored cost must reflect tokens at call time, not post-call mutation
    assert store.costs[0]["cost"] == pytest.approx(expected_cost)


def test_src_package_exposes_record_run():
    """record_run must be importable directly from the src package."""
    from src import record_run as _pkg_record_run
    assert callable(_pkg_record_run)
    assert _pkg_record_run is record_run
