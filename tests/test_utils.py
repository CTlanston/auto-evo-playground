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
