"""Tests for src.utils.slugify — 7 cases covering the slugify contract."""
import pytest

from src.utils import slugify


@pytest.mark.parametrize("inp,expected", [
    ("Hello World", "hello-world"),
    ("foo_bar!baz", "foo-bar-baz"),
    ("a  b--c", "a-b-c"),
    ("--hello--", "hello"),
    ("foo123bar", "foo123bar"),
    ("", ""),
])
def test_slugify_parametrized(inp, expected):
    assert slugify(inp) == expected


def test_slugify_truncation():
    assert slugify("a" * 100, max_len=10) == "a" * 10
