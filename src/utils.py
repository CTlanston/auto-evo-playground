"""Utility helpers — auto-edited by Claude agents."""


def is_palindrome(s: str, case_insensitive: bool = True) -> bool:
    chars = [c for c in s if c.isalnum()]
    if case_insensitive:
        chars = [c.lower() for c in chars]
    return chars == chars[::-1]
