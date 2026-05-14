"""Tests for human_readable_size utility (TDD red phase)."""
import pytest
from src.utils import human_readable_size


@pytest.mark.parametrize("bytes_count, expected", [
    (0, "0 B"),
    (512, "512 B"),
    (1023, "1023 B"),
    (1024, "1.0 KB"),
    (1024 * 1024, "1.0 MB"),
    (1024 * 1024 * 1024, "1.0 GB"),
    (1024 ** 4, "1.0 TB"),
    (1024 ** 4 * 2, "2.0 TB"),
])
def test_human_readable_size(bytes_count, expected):
    assert human_readable_size(bytes_count) == expected
