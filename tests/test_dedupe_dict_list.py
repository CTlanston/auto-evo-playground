import pytest

from src.utils import dedupe_dict_list


def test_empty_list():
    assert dedupe_dict_list([], "id") == []


def test_single_element():
    assert dedupe_dict_list([{"id": 1, "v": "a"}], "id") == [{"id": 1, "v": "a"}]


def test_dedupe_int_key():
    items = [{"id": 1}, {"id": 2}, {"id": 1}, {"id": 3}]
    assert dedupe_dict_list(items, "id") == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_dedupe_string_key():
    items = [{"name": "alice"}, {"name": "bob"}, {"name": "alice"}]
    assert dedupe_dict_list(items, "name") == [{"name": "alice"}, {"name": "bob"}]


def test_missing_key_raises_key_error():
    items = [{"id": 1}, {"x": 2}]
    with pytest.raises(KeyError):
        dedupe_dict_list(items, "id")
