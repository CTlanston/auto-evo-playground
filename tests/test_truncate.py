from src.utils import truncate
from src import truncate as src_truncate


def test_src_package_exposes_truncate():
    assert src_truncate("hello world", 8) == "hello..."


def test_short_string_unchanged():
    assert truncate("hi", 10) == "hi"


def test_truncate_default_suffix():
    assert truncate("hello world", 8) == "hello..."


def test_exact_length_unchanged():
    assert truncate("hello", 5) == "hello"


def test_suffix_fills_entire_length():
    assert truncate("hello world", 3) == "..."


def test_custom_suffix():
    assert truncate("hello world", 8, suffix="!") == "hello w!"


def test_empty_string():
    assert truncate("", 5) == ""


def test_very_long_string_single_char_suffix():
    assert truncate("a" * 1000, 4, suffix="~") == "aaa~"
