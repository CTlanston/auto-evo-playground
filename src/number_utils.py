def clamp(value: float, min_value: float, max_value: float) -> float:
    if min_value > max_value:
        raise ValueError("min_value must not be greater than max_value")
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value
