import pytest
from src.utils import is_palindrome
from src import is_palindrome as src_is_palindrome


def test_racecar():
    assert is_palindrome("racecar") is True


def test_a_man_a_plan_a_canal_panama():
    assert is_palindrome("A man, a plan, a canal: Panama") is True


def test_hello_not_palindrome():
    assert is_palindrome("hello") is False


def test_empty_string():
    assert is_palindrome("") is True


def test_madam_case_insensitive():
    assert is_palindrome("Madam", case_insensitive=True) is True


def test_madam_case_sensitive_false():
    assert is_palindrome("Madam", case_insensitive=False) is False


def test_src_package_exposes_is_palindrome():
    assert src_is_palindrome("racecar") is True
