"""Utility helpers — auto-edited by Claude agents."""


def reverse(s: str) -> str:
    """Return s reversed at Unicode code-point level.

    NFD-normalized strings (combining characters as separate code points) will
    have those combining marks reversed into unexpected positions. Normalize to
    NFC with unicodedata.normalize('NFC', s) before calling if needed.
    """
    return s[::-1]
