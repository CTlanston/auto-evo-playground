"""Run recorder — persists run records and associated cost entries to a store."""
import logging

COST_PER_TOKEN = 0.001


class RunStore:
    def __init__(self):
        self.runs = []
        self.costs = []

    def insert(self, run):
        self.runs.append(dict(run))

    def insert_cost(self, cost_entry):
        self.costs.append(dict(cost_entry))


def record_run(run_data, store):
    store.insert(run_data)
    run_id = run_data.get("id")
    if run_id is None:
        return
    if "tokens" not in run_data:
        return
    tokens = run_data["tokens"]
    if tokens is None:
        return
    if isinstance(tokens, bool) or not isinstance(tokens, (int, float)):
        return
    if tokens < 0:
        logging.warning(
            "record_run: negative tokens=%r for run_id=%r; skipping cost entry",
            tokens,
            run_id,
        )
        return
    store.insert_cost({"run_id": run_id, "cost": tokens * COST_PER_TOKEN})
