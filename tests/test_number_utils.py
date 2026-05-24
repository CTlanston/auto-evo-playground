import pytest

from src.number_utils import clamp


def test_value_within_range_returned_as_is():
    assert clamp(5, 0, 10) == 5


def test_value_below_range_clamped_to_min():
    assert clamp(-3, 0, 10) == 0


def test_value_above_range_clamped_to_max():
    assert clamp(15, 0, 10) == 10


def test_value_equal_to_min_returned():
    assert clamp(0, 0, 10) == 0


def test_value_equal_to_max_returned():
    assert clamp(10, 0, 10) == 10


def test_float_value_within_range():
    assert clamp(2.5, 0.0, 5.0) == 2.5


def test_float_value_below_range():
    assert clamp(-1.5, 0.0, 5.0) == 0.0


def test_float_value_above_range():
    assert clamp(7.5, 0.0, 5.0) == 5.0


def test_mixed_int_and_float_bounds():
    assert clamp(3, 0.0, 5.0) == 3
    assert clamp(3.5, 0, 5) == 3.5


def test_negative_range():
    assert clamp(-5, -10, -1) == -5
    assert clamp(-15, -10, -1) == -10
    assert clamp(0, -10, -1) == -1


def test_min_equals_max_collapses_to_point():
    assert clamp(99, 5, 5) == 5
    assert clamp(0, 5, 5) == 5


def test_raises_when_min_greater_than_max():
    with pytest.raises(ValueError):
        clamp(0, 10, 5)
