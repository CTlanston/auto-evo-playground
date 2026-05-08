# auto-evo-playground

Telemetry metrics aggregator — groups per-server numeric metrics and computes mean/max/min.

## Usage

```python
from src.telemetry_aggregator import aggregate_metrics

payloads = [
    {"server_id": "web-01", "cpu_usage": 0.4, "memory_allocated": 2048},
    {"server_id": "web-01", "cpu_usage": 0.8, "memory_allocated": 3072},
    {"server_id": "db-01",  "cpu_usage": 0.2, "memory_allocated": 8192},
]

result = aggregate_metrics(payloads)
# {
#   "web-01": {"cpu_usage": {"mean": 0.6, "max": 0.8, "min": 0.4}, ...},
#   "db-01":  {"cpu_usage": {"mean": 0.2, "max": 0.2, "min": 0.2}, ...},
# }
```

Payloads missing `server_id`, or with `None`/non-numeric/boolean metric values, are skipped with a `logging.WARNING`.

## Tests

```bash
pytest --cov=src/telemetry_aggregator --cov-fail-under=100
```
