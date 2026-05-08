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


def test_reverse_nfd():
    # NFD form: 'e' + combining acute accent (U+0301) = 5 code points
    cafe_nfd = "café"
    # Expect NFC-aware reversal — this intentionally fails to drive the feat commit
    assert reverse(cafe_nfd) == "\xe9fac", (
        f"Expected NFC-aware result but got {reverse(cafe_nfd)!r}"
    )
