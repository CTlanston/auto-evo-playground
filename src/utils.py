"""Utility helpers — auto-edited by Claude agents."""
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email_simple(s: str) -> bool:
    return bool(_EMAIL_RE.match(s))
