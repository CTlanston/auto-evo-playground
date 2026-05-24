def slugify(text: str) -> str:
    text = text.lower()
    out = []
    for ch in text:
        if ch.isalnum():
            out.append(ch)
        elif ch.isspace() or ch in ("-", "_"):
            out.append("-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace to a single space; strip ends."""
    return " ".join(text.split())
