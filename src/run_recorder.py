"""Run recorder — persists run records to a store."""


def record_run(run_data, store):
    store.insert(run_data)
