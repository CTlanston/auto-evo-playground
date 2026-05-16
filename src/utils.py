"""Utility helpers — auto-edited by Claude agents."""


def unique_preserve_order(items: list) -> list:
    """Return items with duplicates removed, preserving first-appearance order.

    All elements must be hashable; unhashable types (list, dict) raise TypeError.
    Equal values (e.g. 1, True, 1.0) are deduplicated per Python hash/equality rules.
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
