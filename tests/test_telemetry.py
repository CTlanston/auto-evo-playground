"""Tests for src.telemetry_aggregator.aggregate_metrics."""
import sys
from unittest.mock import patch

from src.telemetry_aggregator import aggregate_metrics
from src import aggregate_metrics as _pkg_aggregate_metrics


def test_src_package_exposes_aggregate_metrics():
    """aggregate_metrics must be importable directly from the src package."""
    assert callable(_pkg_aggregate_metrics)
    assert _pkg_aggregate_metrics is aggregate_metrics


# ---------------------------------------------------------------------------
# Step 1 – Happy-path tests
# ---------------------------------------------------------------------------

def test_basic_grouping_and_stats():
    """Two payloads for srv-01, one for srv-02; check mean/max/min."""
    payloads = [
        {"server_id": "srv-01", "cpu_usage": 40.0, "memory_allocated": 1024.0},
        {"server_id": "srv-01", "cpu_usage": 80.0, "memory_allocated": 2048.0},
        {"server_id": "srv-02", "cpu_usage": 50.0, "memory_allocated": 512.0},
    ]
    result = aggregate_metrics(payloads)

    assert result["srv-01"]["cpu_usage"] == {"mean": 60.0, "max": 80.0, "min": 40.0}
    assert result["srv-02"]["cpu_usage"] == {"mean": 50.0, "max": 50.0, "min": 50.0}
    assert result["srv-01"]["memory_allocated"] == {
        "mean": 1536.0, "max": 2048.0, "min": 1024.0
    }
    assert result["srv-02"]["memory_allocated"] == {
        "mean": 512.0, "max": 512.0, "min": 512.0
    }


def test_single_server_single_payload():
    """Single payload: mean == max == min."""
    payloads = [{"server_id": "srv-99", "cpu_usage": 75.0}]
    result = aggregate_metrics(payloads)
    assert result["srv-99"]["cpu_usage"] == {"mean": 75.0, "max": 75.0, "min": 75.0}


def test_integer_metric_values():
    """Integer metric values should be treated as numeric."""
    payloads = [
        {"server_id": "box-01", "latency_ms": 10},
        {"server_id": "box-01", "latency_ms": 30},
    ]
    result = aggregate_metrics(payloads)
    assert result["box-01"]["latency_ms"] == {"mean": 20.0, "max": 30, "min": 10}


def test_result_keys_match_server_ids():
    """Top-level keys of result must exactly match server_ids seen."""
    payloads = [
        {"server_id": "alpha", "x": 1.0},
        {"server_id": "beta", "x": 2.0},
        {"server_id": "gamma", "x": 3.0},
    ]
    result = aggregate_metrics(payloads)
    assert set(result.keys()) == {"alpha", "beta", "gamma"}


# ---------------------------------------------------------------------------
# Step 2 – Edge-case tests
# ---------------------------------------------------------------------------

def test_empty_payload_list_returns_empty_dict():
    """Empty input must produce an empty dict."""
    assert aggregate_metrics([]) == {}


def test_missing_server_id_is_dropped_with_warning():
    """Payload without 'server_id' is silently dropped; a warning is logged."""
    bad = {"cpu_usage": 55.0}
    good = {"server_id": "srv-10", "cpu_usage": 30.0}

    with patch("src.telemetry_aggregator.logging") as mock_log:
        result = aggregate_metrics([bad, good])

    mock_log.warning.assert_called_once()
    assert list(result.keys()) == ["srv-10"]
    assert result["srv-10"]["cpu_usage"] == {"mean": 30.0, "max": 30.0, "min": 30.0}


def test_none_metric_value_is_dropped_with_warning():
    """Payload where a metric value is None is dropped; a warning is logged."""
    bad = {"server_id": "srv-20", "cpu_usage": None}
    good = {"server_id": "srv-20", "cpu_usage": 70.0}

    with patch("src.telemetry_aggregator.logging") as mock_log:
        result = aggregate_metrics([bad, good])

    mock_log.warning.assert_called_once()
    assert result["srv-20"]["cpu_usage"] == {"mean": 70.0, "max": 70.0, "min": 70.0}


def test_non_numeric_metric_value_is_dropped_with_warning():
    """Payload where a metric value is a string is dropped; a warning is logged."""
    bad = {"server_id": "srv-30", "cpu_usage": "high"}
    good = {"server_id": "srv-30", "cpu_usage": 45.0}

    with patch("src.telemetry_aggregator.logging") as mock_log:
        result = aggregate_metrics([bad, good])

    mock_log.warning.assert_called_once()
    assert result["srv-30"]["cpu_usage"] == {"mean": 45.0, "max": 45.0, "min": 45.0}


def test_extreme_outlier_values():
    """sys.float_info.max, 0.0, and negative values are handled correctly."""
    big = sys.float_info.max
    payloads = [
        {"server_id": "srv-ext", "metric": big},
        {"server_id": "srv-ext", "metric": 0.0},
        {"server_id": "srv-ext", "metric": -1000.0},
    ]
    result = aggregate_metrics(payloads)
    stats = result["srv-ext"]["metric"]
    assert stats["max"] == big
    assert stats["min"] == -1000.0
    expected_mean = (big + 0.0 + (-1000.0)) / 3
    assert stats["mean"] == expected_mean


def test_multiple_bad_payloads_all_logged_valid_still_aggregated():
    """Multiple malformed payloads each trigger a warning; valid ones still appear."""
    payloads = [
        {"cpu_usage": 10.0},                          # missing server_id
        {"server_id": "srv-50", "cpu_usage": None},   # None value
        {"server_id": "srv-50", "cpu_usage": "oops"}, # non-numeric
        {"server_id": "srv-50", "cpu_usage": 88.0},   # valid
    ]

    with patch("src.telemetry_aggregator.logging") as mock_log:
        result = aggregate_metrics(payloads)

    assert mock_log.warning.call_count == 3
    assert result["srv-50"]["cpu_usage"] == {"mean": 88.0, "max": 88.0, "min": 88.0}


def test_bool_metric_value_is_dropped_with_warning():
    """bool values must be rejected (bool subclasses int, so explicit check required)."""
    bad = {"server_id": "srv-60", "active": True}
    good = {"server_id": "srv-60", "cpu_usage": 55.0}

    with patch("src.telemetry_aggregator.logging") as mock_log:
        result = aggregate_metrics([bad, good])

    mock_log.warning.assert_called_once()
    # 'active' must not appear; only the valid payload's metric should be present
    assert "active" not in result.get("srv-60", {})
    assert result["srv-60"]["cpu_usage"] == {"mean": 55.0, "max": 55.0, "min": 55.0}


def test_nan_metric_value_is_dropped_with_warning():
    """float('nan') passes isinstance check but poisons stats; must be rejected."""
    bad = {"server_id": "srv-70", "cpu_usage": float("nan")}
    good = {"server_id": "srv-70", "cpu_usage": 60.0}

    with patch("src.telemetry_aggregator.logging") as mock_log:
        result = aggregate_metrics([bad, good])

    mock_log.warning.assert_called_once()
    assert result["srv-70"]["cpu_usage"] == {"mean": 60.0, "max": 60.0, "min": 60.0}


def test_payload_with_no_metrics_is_dropped_with_warning():
    """A payload that has server_id but no numeric metrics is dropped with a warning."""
    empty_metrics = {"server_id": "srv-80"}
    good = {"server_id": "srv-80", "cpu_usage": 42.0}

    with patch("src.telemetry_aggregator.logging") as mock_log:
        result = aggregate_metrics([empty_metrics, good])

    mock_log.warning.assert_called_once()
    assert result["srv-80"]["cpu_usage"] == {"mean": 42.0, "max": 42.0, "min": 42.0}


def test_whole_payload_dropped_when_any_metric_is_invalid():
    """If one metric in a payload is invalid, the entire payload is dropped (not just that key)."""
    mixed = {"server_id": "srv-90", "cpu_usage": 50.0, "mem": None}
    good = {"server_id": "srv-90", "cpu_usage": 30.0, "mem": 1024.0}

    with patch("src.telemetry_aggregator.logging") as mock_log:
        result = aggregate_metrics([mixed, good])

    mock_log.warning.assert_called_once()
    # Only the valid payload contributes; the mixed one is dropped entirely
    assert result["srv-90"]["cpu_usage"] == {"mean": 30.0, "max": 30.0, "min": 30.0}
    assert result["srv-90"]["mem"] == {"mean": 1024.0, "max": 1024.0, "min": 1024.0}
