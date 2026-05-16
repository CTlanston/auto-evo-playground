import pytest

from src.utils import unique_preserve_order


def test_empty_list():
    assert unique_preserve_order([]) == []


def test_no_duplicates():
    assert unique_preserve_order([1, 2, 3]) == [1, 2, 3]


def test_duplicates_preserve_first_appearance():
    assert unique_preserve_order([1, 2, 3, 2, 1]) == [1, 2, 3]


def test_strings():
    assert unique_preserve_order(["a", "b", "a", "c"]) == ["a", "b", "c"]


def test_none_values():
    assert unique_preserve_order([None, 1, None, 2]) == [None, 1, 2]


def test_all_duplicates():
    assert unique_preserve_order([2, 2, 2]) == [2]


def test_type_coercion_treats_equal_values_as_duplicates():
    # Python equality/hash semantics: 1 == True == 1.0, so only first survives
    assert unique_preserve_order([1, True, 1.0]) == [1]


def test_unhashable_items_raise_type_error():
    with pytest.raises(TypeError):
        unique_preserve_order([[1], [2]])


def test_string_input_returns_unique_chars():
    # Current permissive behavior: strings iterate as chars
    assert unique_preserve_order("abac") == ["a", "b", "c"]


def test_generator_input_is_consumed_once():
    # Current permissive behavior: any iterable works, generators consumed once
    assert unique_preserve_order(x for x in [1, 2, 1, 3]) == [1, 2, 3]
