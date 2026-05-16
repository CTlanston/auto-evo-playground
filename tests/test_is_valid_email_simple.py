import pytest
from src.utils import is_valid_email_simple
from src import is_valid_email_simple as _pkg_export  # noqa: F401


@pytest.mark.parametrize("email,expected", [
    # valid addresses
    ("user@example.com", True),
    ("user.name@example.com", True),
    ("user+tag@example.org", True),
    ("firstname.lastname@sub.domain.co", True),
    ("a@b.io", True),
    ("user123@domain.net", True),
    # invalid addresses
    ("notanemail", False),
    ("", False),
    ("@domain.com", False),
    ("user@", False),
    ("user@domain", False),
    ("user@@domain.com", False),
    ("user@domain.", False),
    ("user @domain.com", False),
    ("user@.domain.com", False),
    ("user@domain..com", False),
])
def test_is_valid_email_simple(email, expected):
    assert is_valid_email_simple(email) is expected
