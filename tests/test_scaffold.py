"""Verify human_readable_size is importable as part of the project scaffold."""


def test_human_readable_size_importable():
    """human_readable_size must be importable from src.utils."""
    from src.utils import human_readable_size
    assert callable(human_readable_size), "human_readable_size must be callable"
