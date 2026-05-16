"""Utility helpers — auto-edited by Claude agents."""

import re


def is_valid_email_simple(s: str) -> bool:
    """Return True if s looks like a valid email address (simple heuristic)."""
    return bool(re.fullmatch(r"[^@\s]+@[^@\s.]+(\.[^@\s.]+)*\.[^@\s.]{2,}", s))
