"""Utility helpers — auto-edited by Claude agents."""


def reverse(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError(f"reverse() requires a str, got {type(s).__name__}")
    return s[::-1]
