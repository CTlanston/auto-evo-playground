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
