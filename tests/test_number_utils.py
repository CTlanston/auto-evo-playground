import pytest

from src.number_utils import clamp


def test_within_range_returns_value():
    assert clamp(5, 0, 10) == 5


def test_below_range_returns_min():
    assert clamp(-1, 0, 10) == 0


def test_above_range_returns_max():
    assert clamp(11, 0, 10) == 10


def test_equal_to_min_returns_value():
    assert clamp(0, 0, 10) == 0


def test_equal_to_max_returns_value():
    assert clamp(10, 0, 10) == 10


def test_min_equals_max_returns_that_value():
    assert clamp(5, 7, 7) == 7
    assert clamp(7, 7, 7) == 7
    assert clamp(9, 7, 7) == 7


def test_float_within_range():
    assert clamp(1.5, 0.0, 2.0) == 1.5


def test_float_below_range():
    assert clamp(-0.5, 0.0, 1.0) == 0.0


def test_float_above_range():
    assert clamp(2.5, 0.0, 1.0) == 1.0


def test_mixed_int_float_inputs():
    assert clamp(1, 0.0, 2.0) == 1
    assert clamp(2.5, 0, 2) == 2


def test_negative_range():
    assert clamp(-5, -10, -1) == -5
    assert clamp(-20, -10, -1) == -10
    assert clamp(0, -10, -1) == -1


def test_raises_when_min_greater_than_max():
    with pytest.raises(ValueError):
        clamp(5, 10, 0)


def test_raises_independent_of_value():
    with pytest.raises(ValueError):
        clamp(0, 10, 0)
