"""Full pytest suite for aggregate_metrics() — TDD red phase."""
import logging
import pytest
from src.telemetry_aggregator import aggregate_metrics


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

def test_single_payload_returns_correct_structure():
    payloads = [
        {"server_id": "s1", "cpu_usage": 0.5, "memory_allocated": 1024}
    ]
    result = aggregate_metrics(payloads)
    assert "s1" in result
    assert "cpu_usage" in result["s1"]
    assert set(result["s1"]["cpu_usage"].keys()) == {"mean", "max", "min"}


def test_single_payload_mean_max_min_equal():
    payloads = [
        {"server_id": "s1", "cpu_usage": 0.8, "memory_allocated": 512}
    ]
    result = aggregate_metrics(payloads)
    cpu = result["s1"]["cpu_usage"]
    assert cpu["mean"] == pytest.approx(0.8)
    assert cpu["max"] == pytest.approx(0.8)
    assert cpu["min"] == pytest.approx(0.8)


def test_multiple_payloads_same_server_mean_max_min():
    payloads = [
        {"server_id": "s1", "cpu_usage": 0.2, "memory_allocated": 100},
        {"server_id": "s1", "cpu_usage": 0.6, "memory_allocated": 300},
        {"server_id": "s1", "cpu_usage": 1.0, "memory_allocated": 500},
    ]
    result = aggregate_metrics(payloads)
    cpu = result["s1"]["cpu_usage"]
    assert cpu["mean"] == pytest.approx(0.6)
    assert cpu["max"] == pytest.approx(1.0)
    assert cpu["min"] == pytest.approx(0.2)
    mem = result["s1"]["memory_allocated"]
    assert mem["mean"] == pytest.approx(300.0)
    assert mem["max"] == pytest.approx(500.0)
    assert mem["min"] == pytest.approx(100.0)


def test_multiple_servers_grouped_independently():
    payloads = [
        {"server_id": "s1", "cpu_usage": 0.4, "memory_allocated": 200},
        {"server_id": "s2", "cpu_usage": 0.9, "memory_allocated": 800},
        {"server_id": "s1", "cpu_usage": 0.6, "memory_allocated": 400},
    ]
    result = aggregate_metrics(payloads)
    assert set(result.keys()) == {"s1", "s2"}
    assert result["s1"]["cpu_usage"]["mean"] == pytest.approx(0.5)
    assert result["s2"]["cpu_usage"]["mean"] == pytest.approx(0.9)


def test_returns_empty_dict_for_empty_list():
    assert aggregate_metrics([]) == {}


def test_extreme_outlier_values():
    payloads = [
        {"server_id": "s1", "cpu_usage": 1e-9, "memory_allocated": 1},
        {"server_id": "s1", "cpu_usage": 1e9, "memory_allocated": 10**9},
    ]
    result = aggregate_metrics(payloads)
    cpu = result["s1"]["cpu_usage"]
    assert cpu["max"] == pytest.approx(1e9)
    assert cpu["min"] == pytest.approx(1e-9)
    assert cpu["mean"] == pytest.approx((1e-9 + 1e9) / 2)


# ---------------------------------------------------------------------------
# Edge / malformed payload tests
# ---------------------------------------------------------------------------

def test_missing_server_id_skipped(caplog):
    payloads = [
        {"cpu_usage": 0.5, "memory_allocated": 100},
        {"server_id": "s1", "cpu_usage": 0.3, "memory_allocated": 200},
    ]
    with caplog.at_level(logging.WARNING):
        result = aggregate_metrics(payloads)
    assert set(result.keys()) == {"s1"}
    assert any("server_id" in msg.lower() or "missing" in msg.lower() for msg in caplog.messages)


def test_null_metric_value_skipped(caplog):
    payloads = [
        {"server_id": "s1", "cpu_usage": None, "memory_allocated": 256},
        {"server_id": "s1", "cpu_usage": 0.5, "memory_allocated": 512},
    ]
    with caplog.at_level(logging.WARNING):
        result = aggregate_metrics(payloads)
    # cpu_usage None entry skipped; only 0.5 remains
    cpu = result["s1"]["cpu_usage"]
    assert cpu["mean"] == pytest.approx(0.5)
    # memory_allocated: both entries valid
    mem = result["s1"]["memory_allocated"]
    assert mem["mean"] == pytest.approx(384.0)


def test_non_numeric_metric_value_skipped(caplog):
    payloads = [
        {"server_id": "s1", "cpu_usage": "high", "memory_allocated": 128},
        {"server_id": "s1", "cpu_usage": 0.7, "memory_allocated": 256},
    ]
    with caplog.at_level(logging.WARNING):
        result = aggregate_metrics(payloads)
    cpu = result["s1"]["cpu_usage"]
    assert cpu["mean"] == pytest.approx(0.7)


def test_all_payloads_malformed_returns_empty(caplog):
    payloads = [
        {"cpu_usage": 0.5},
        {"memory_allocated": 100},
    ]
    with caplog.at_level(logging.WARNING):
        result = aggregate_metrics(payloads)
    assert result == {}


def test_metric_entirely_null_not_included_in_result(caplog):
    """If all values for a metric on a server are null/non-numeric, that metric key is absent."""
    payloads = [
        {"server_id": "s1", "cpu_usage": None, "memory_allocated": 512},
    ]
    with caplog.at_level(logging.WARNING):
        result = aggregate_metrics(payloads)
    assert "cpu_usage" not in result["s1"]
    assert "memory_allocated" in result["s1"]


def test_integer_metrics_treated_as_numeric():
    payloads = [
        {"server_id": "s1", "cpu_usage": 1, "memory_allocated": 100},
        {"server_id": "s1", "cpu_usage": 3, "memory_allocated": 300},
    ]
    result = aggregate_metrics(payloads)
    assert result["s1"]["cpu_usage"]["mean"] == pytest.approx(2.0)
