"""TDD tests for src.utils.parse_kv_line — 6 cases from the Issue Spec."""
import pytest

from src.utils import parse_kv_line


def test_basic_key_value():
    assert parse_kv_line("key=value") == ("key", "value")


def test_whitespace_stripped():
    assert parse_kv_line(" key = value ") == ("key", "value")


def test_empty_value():
    assert parse_kv_line("key=") == ("key", "")


def test_empty_key():
    assert parse_kv_line("=value") == ("", "value")


def test_multiple_equals_splits_on_first():
    assert parse_kv_line("key=a=b") == ("key", "a=b")


def test_no_equals_raises_value_error():
    with pytest.raises(ValueError):
        parse_kv_line("no-equals-here")
