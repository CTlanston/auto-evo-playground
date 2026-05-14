"""Utility helpers — auto-edited by Claude agents."""


def flatten_one_level(nested: list) -> list:
    for item in nested:
        if not isinstance(item, list):
            raise TypeError(
                f"All elements must be lists, got {type(item).__name__}"
            )
    return [elem for sublist in nested for elem in sublist]
