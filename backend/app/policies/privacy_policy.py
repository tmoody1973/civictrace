"""Deny-list patterns for personal data. Public-record figures (dollars, dates, files) pass."""

from __future__ import annotations

import re

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "phone": re.compile(r"(?<![\d,.$])\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\d,])"),
}


def find_pii(text: str) -> list[str]:
    return [kind for kind, pattern in PII_PATTERNS.items() if pattern.search(text)]
