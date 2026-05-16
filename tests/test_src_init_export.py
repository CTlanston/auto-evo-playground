from src import is_palindrome


def test_is_palindrome_importable_from_src_package():
    assert is_palindrome("racecar") is True
