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


# MPS privacy boundary: an inquiry may never ask about individual students or personnel.
# ponytail: word list, fail-closed; a refused public-facing word (e.g. "medical campus")
# lands in HUMAN_REVIEW rather than shipping — acceptable ceiling for the MVP.
# "family" is deliberately absent: "multi-family housing" is routine TIF language.
RESTRICTED_SCOPE_TERMS: tuple[str, ...] = (
    "student",
    "students",
    "pupil",
    "pupils",
    "attendance",
    "grades",
    "discipline",
    "disciplinary",
    "disability",
    "disabilities",
    "personnel",
    "medical",
    "home address",
)
_RESTRICTED = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in RESTRICTED_SCOPE_TERMS) + r")\b", re.I
)


def find_restricted_scope(text: str) -> list[str]:
    return sorted({match.lower() for match in _RESTRICTED.findall(text)})
