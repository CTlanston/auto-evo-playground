"""Tests for src.utils.safe_int."""
import pytest

from src.utils import safe_int


@pytest.mark.parametrize(
    "value, default, expected",
    [
        (3, 0, 3),            # int pass-through
        (3.9, 0, 3),          # float truncation
        (None, 0, 0),         # None → default
        ("42", 0, 42),        # string parse
        ("abc", 0, 0),        # ValueError → default
        ("abc", 99, 99),      # ValueError → custom default
        ("  -5  ", 0, -5),    # strip-then-parse
    ],
)
def test_safe_int(value, default, expected):
    assert safe_int(value, default) == expected
