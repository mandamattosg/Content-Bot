from __future__ import annotations

import re
from html import unescape


_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def strip_html(value: str) -> str:
    cleaned_value = _HTML_TAG_PATTERN.sub(" ", value)
    return unescape(cleaned_value)


def compact_whitespace(value: str) -> str:
    return _WHITESPACE_PATTERN.sub(" ", value).strip()


def normalize_text(value: str) -> str:
    return compact_whitespace(strip_html(value))


def truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"
