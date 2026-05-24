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


def dedupe_words(text: str) -> str:
    """Remove consecutive duplicate words from ``text``.

    Words are compared case-insensitively (via ``casefold``) but the
    casing of the first occurrence in each run is preserved. Runs of
    whitespace collapse to a single space; leading and trailing
    whitespace is removed. Returns ``""`` for empty or whitespace-only
    input. Punctuation is treated as part of the adjacent word.
    """
    tokens = text.split()
    if not tokens:
        return ""
    out = [tokens[0]]
    prev_key = tokens[0].casefold()
    for tok in tokens[1:]:
        key = tok.casefold()
        if key != prev_key:
            out.append(tok)
            prev_key = key
    return " ".join(out)
