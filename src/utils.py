"""Utility helpers — auto-edited by Claude agents."""


def human_readable_size(bytes_count: int) -> str:
    """Return a human-readable string for a byte count using binary (1024-based) units."""
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_count < 1024:
            if unit == "B":
                return f"{bytes_count} B"
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} TB"
