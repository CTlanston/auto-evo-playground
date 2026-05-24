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
    tokens = text.split()
    result = []
    for tok in tokens:
        if result and tok.lower() == result[-1].lower():
            continue
        result.append(tok)
    return " ".join(result)
