"""Utility helpers — auto-edited by Claude agents."""


def parse_kv_line(line: str) -> tuple[str, str]:
    if "=" not in line:
        raise ValueError(f"No '=' found in line: {line!r}")
    key, value = line.split("=", 1)
    return key.strip(), value.strip()
