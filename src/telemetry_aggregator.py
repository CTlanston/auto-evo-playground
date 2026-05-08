"""Telemetry metrics aggregator."""
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def aggregate_metrics(payloads):
    """Aggregate per-server numeric metrics from a list of payload dicts.

    Each payload must have a 'server_id' key and one or more numeric metric
    keys.  Payloads missing 'server_id' are skipped with a warning.  Individual
    metric values that are None or non-numeric are also skipped with a warning.

    Returns a nested dict: {server_id: {metric: {mean, max, min}}}.
    """
    if not payloads:
        return {}

    # Accumulate raw values per (server, metric)
    buckets = defaultdict(lambda: defaultdict(list))

    for payload in payloads:
        if "server_id" not in payload:
            logger.warning("payload missing server_id key, skipping: %s", payload)
            continue

        server_id = payload["server_id"]
        for key, value in payload.items():
            if key == "server_id":
                continue
            if value is None:
                logger.warning(
                    "null value for metric '%s' on server '%s', skipping",
                    key, server_id,
                )
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                logger.warning(
                    "non-numeric value %r for metric '%s' on server '%s', skipping",
                    value, key, server_id,
                )
                continue
            buckets[server_id][key].append(value)

    result = {}
    for server_id, metrics in buckets.items():
        result[server_id] = {}
        for metric, values in metrics.items():
            result[server_id][metric] = {
                "mean": sum(values) / len(values),
                "max": max(values),
                "min": min(values),
            }

    return result
