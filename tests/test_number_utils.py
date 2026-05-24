import pytest

from src.number_utils import clamp


def test_returns_value_when_in_range():
    assert clamp(5, 0, 10) == 5


def test_returns_min_when_below_range():
    assert clamp(-3, 0, 10) == 0


def test_returns_max_when_above_range():
    assert clamp(42, 0, 10) == 10


def test_equal_to_min_returns_value():
    assert clamp(0, 0, 10) == 0


def test_equal_to_max_returns_value():
    assert clamp(10, 0, 10) == 10


def test_supports_floats():
    assert clamp(1.5, 0.0, 2.0) == 1.5
    assert clamp(-0.1, 0.0, 2.0) == 0.0
    assert clamp(2.5, 0.0, 2.0) == 2.0


def test_supports_mixed_int_and_float():
    assert clamp(1, 0.0, 2.0) == 1
    assert clamp(3.0, 0, 2) == 2


def test_degenerate_range_min_equals_max():
    assert clamp(5, 3, 3) == 3
    assert clamp(1, 3, 3) == 3
    assert clamp(9, 3, 3) == 3


def test_raises_when_min_greater_than_max():
    with pytest.raises(ValueError):
        clamp(5, 10, 0)
