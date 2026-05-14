"""Tests for src.utils.flatten_one_level."""
import pytest
from src.utils import flatten_one_level


def test_empty_list():
    assert flatten_one_level([]) == []


def test_basic_flatten():
    assert flatten_one_level([[1, 2], [3, 4]]) == [1, 2, 3, 4]


def test_single_element_sublist():
    assert flatten_one_level([[42]]) == [42]


def test_sublist_with_empty():
    assert flatten_one_level([[], [1, 2]]) == [1, 2]


def test_nested_list_one_level():
    assert flatten_one_level([[1, [2]], [3]]) == [1, [2], 3]


def test_type_error_on_flat_input():
    with pytest.raises(TypeError):
        flatten_one_level([1, 2, 3])
