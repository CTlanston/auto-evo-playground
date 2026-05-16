"""Tests for src.utils.is_valid_email_simple — TDD red phase."""
import pytest

from src.utils import is_valid_email_simple


@pytest.mark.parametrize(
    "address, expected",
    [
        ("user@example.com", True),
        ("user.name+tag@example.co.uk", True),
        ("notanemail", False),
        ("@nodomain.com", False),
        ("user@", False),
        ("user@domain", False),
        ("user @example.com", False),
    ],
)
def test_is_valid_email_simple(address, expected):
    assert is_valid_email_simple(address) is expected
