"""Simple PII pattern gate on text that is about to become evidence."""

from __future__ import annotations

import pytest

from app.policies.privacy_policy import find_pii


@pytest.mark.parametrize(
    "text",
    [
        "TOTAL Capital Project Costs $700,000",
        "Authorized expenditure (excluding interest): $763,750 Authorizing resolution(s): #240382",
        "created 2024-07-02, file 260433, $2,345,000",
    ],
)
def test_public_record_figures_are_not_pii(text: str) -> None:
    assert find_pii(text) == []


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("resident SSN 123-45-6789 on file", "ssn"),
        ("contact jane.doe@example.com for details", "email"),
        ("call (414) 555-0199 to confirm", "phone"),
        ("call 414-555-0199 to confirm", "phone"),
    ],
)
def test_pii_patterns_are_found(text: str, kind: str) -> None:
    assert kind in find_pii(text)
