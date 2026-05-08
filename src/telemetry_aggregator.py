"""Telemetry metrics aggregator — stdlib only."""
import logging
import math


def aggregate_metrics(payloads):
    """Group payloads by server_id and compute mean/max/min for each numeric metric.

    Payloads missing 'server_id', containing no numeric metrics, or containing a
    None / bool / non-numeric / non-finite metric value are skipped with a warning.

    Returns a dict keyed by server_id; each value is a dict of
    metric_name -> {'mean': float, 'max': number, 'min': number}.
    """
    if not payloads:
        return {}

    groups = {}
    for payload in payloads:
        if "server_id" not in payload:
            logging.warning("Payload missing 'server_id'; skipping: %r", payload)
            continue

        sid = payload["server_id"]

        # Collect non-server_id keys to detect empty-metrics payloads
        metric_items = [(k, v) for k, v in payload.items() if k != "server_id"]

        if not metric_items:
            logging.warning(
                "Payload for server_id=%r has no metric keys; skipping payload", sid
            )
            continue

        valid = True
        for key, value in metric_items:
            if (
                value is None
                or isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                logging.warning(
                    "Payload for server_id=%r has non-numeric value for %r (%r); skipping payload",
                    sid, key, value,
                )
                valid = False
                break

        if not valid:
            continue

        if sid not in groups:
            groups[sid] = {}
        for key, value in metric_items:
            if key not in groups[sid]:
                groups[sid][key] = []
            groups[sid][key].append(value)

    result = {}
    for sid, metrics in groups.items():
        result[sid] = {}
        for metric, values in metrics.items():
            n = len(values)
            result[sid][metric] = {
                "mean": sum(values) / n,
                "max": max(values),
                "min": min(values),
            }
    return result
