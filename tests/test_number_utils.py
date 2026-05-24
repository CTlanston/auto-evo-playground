import pytest

from src.number_utils import clamp


def test_value_within_range_returned_unchanged():
    assert clamp(5, 0, 10) == 5


def test_value_below_min_returns_min():
    assert clamp(-3, 0, 10) == 0


def test_value_above_max_returns_max():
    assert clamp(15, 0, 10) == 10


def test_value_equal_to_min_returned():
    assert clamp(0, 0, 10) == 0


def test_value_equal_to_max_returned():
    assert clamp(10, 0, 10) == 10


def test_supports_floats():
    assert clamp(1.5, 0.0, 2.0) == 1.5
    assert clamp(2.5, 0.0, 2.0) == 2.0
    assert clamp(-0.5, 0.0, 2.0) == 0.0


def test_supports_mixed_int_float():
    assert clamp(1, 0.0, 2.0) == 1


def test_min_equals_max_collapses_to_that_value():
    assert clamp(5, 3, 3) == 3
    assert clamp(1, 3, 3) == 3
    assert clamp(9, 3, 3) == 3


def test_raises_value_error_when_min_greater_than_max():
    with pytest.raises(ValueError):
        clamp(5, 10, 0)
