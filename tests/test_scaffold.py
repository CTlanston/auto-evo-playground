def test_packages_importable():
    import importlib

    src_mod = importlib.import_module("src")
    tests_mod = importlib.import_module("tests")
    assert src_mod.__name__ == "src"
    assert tests_mod.__name__ == "tests"
    assert callable(src_mod.aggregate_metrics)
    assert callable(src_mod.record_run)
