"""Run recorder — persists run records and cost entries to a store."""

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
    if "tokens" not in run_data:
        return
    tokens = run_data["tokens"]
    store.insert_cost({"run_id": run_data.get("id"), "cost": tokens * COST_PER_TOKEN})
