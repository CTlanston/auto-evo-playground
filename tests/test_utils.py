"""Unit tests for src.utils covering reverse(s) edge cases."""

import pytest

from src.utils import reverse


def test_reverse_basic():
    assert reverse("hello") == "olleh"


def test_reverse_empty():
    assert reverse("") == ""


def test_reverse_single_char():
    assert reverse("a") == "a"


def test_reverse_unicode():
    assert reverse("こんにちは") == "はちにんこ"
    assert reverse("café") == "éfac"


def test_reverse_none_raises():
    with pytest.raises(TypeError, match="reverse\\(\\) requires a str"):
        reverse(None)


def test_reverse_int_raises():
    with pytest.raises(TypeError, match="reverse\\(\\) requires a str"):
        reverse(123)
