"""Unit tests for src.utils covering reverse(s) edge cases."""

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
    # NFD: 'e' + combining acute U+0301 = 5 code points; accent lands at front after reversal
    # Callers must normalize to NFC first if grapheme-cluster correctness is required.
    cafe_nfd = "café"
    assert reverse(cafe_nfd) == "́efac"
