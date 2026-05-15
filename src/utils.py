"""Utility helpers — auto-edited by Claude agents."""
import re


def slugify(s, max_len=80):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s[:max_len]
