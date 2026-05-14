"""Utility helpers — auto-edited by Claude agents."""


def dedupe_dict_list(items: list, key: str) -> list:
    seen = set()
    result = []
    for item in items:
        val = item[key]
        if val not in seen:
            seen.add(val)
            result.append(item)
    return result
