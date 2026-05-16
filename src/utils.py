"""Utility helpers — auto-edited by Claude agents."""


def human_readable_size(bytes_count: int) -> str:
    """Return a human-readable string for a byte count (binary 1024-based units, TB ceiling).

    bytes_count should be a non-negative integer; behaviour for negatives is undefined.
    """
    size = float(bytes_count)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            if unit == "B":
                return f"{int(size)} B"
            formatted = f"{size:.1f}"
            if float(formatted) < 1024:
                return f"{formatted} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
