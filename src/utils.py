"""Utility helpers — auto-edited by Claude agents."""


def safe_int(s, default: int = 0) -> int:
    if isinstance(s, int) and not isinstance(s, bool):
        return s
    if isinstance(s, float):
        return int(s)
    if s is None:
        return default
    try:
        return int(str(s).strip())
    except (ValueError, TypeError):
        return default
