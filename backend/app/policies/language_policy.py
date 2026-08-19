"""Deterministic guard for CLAUDE.md rule 4: no unsupported allegations in user-facing statements.

Applied to the neutral_statement only. The verbatim excerpt is the public record; never filtered.
This catches words, not meaning; faithfulness of statement to quote is the Quality Reviewer's job.
"""

from __future__ import annotations

import re

ALLEGATION_TERMS: tuple[str, ...] = (
    "fraud",
    "fraudulent",
    "corrupt",
    "corruption",
    "illegal",
    "illegally",
    "unlawful",
    "crime",
    "criminal",
    "negligent",
    "negligence",
    "misconduct",
    "misled",
    "mislead",
    "lied",
    "lying",
    "cover-up",
    "coverup",
    "cover up",
    "covering up",
    "kickback",
    "bribe",
    "bribery",
    "embezzle",
    "embezzlement",
    "scandal",
    "broke its promise",
    "broken promise",
)
_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in ALLEGATION_TERMS) + r")\b", re.I
)


def find_allegation_language(text: str) -> list[str]:
    return sorted({match.lower() for match in _PATTERN.findall(text)})


CAUSAL_PHRASES: tuple[str, ...] = (
    "because the",
    "caused by",
    "caused",
    "as a result of",
    "due to the developer",
    "due to the city",
    "led to",
    "resulted in",
    "failed to",
    "mismanaged",
)
_CAUSAL = re.compile(r"\b(" + "|".join(re.escape(term) for term in CAUSAL_PHRASES) + r")\b", re.I)


def find_causal_language(text: str) -> list[str]:
    """A Decision Delta states what changed, never why. Cause is for humans with more record."""
    return sorted({match.lower() for match in _CAUSAL.findall(text)})
