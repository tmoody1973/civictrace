from __future__ import annotations

import pytest

from app.policies.language_policy import find_allegation_language


@pytest.mark.parametrize(
    "text",
    [
        "The 2024 Project Plan sets TOTAL Capital Project Costs at an up-to amount of $700,000.",
        "Amendment No. 1 (2026) states the City shall fund an estimated $2,345,000.",
        "The 'Completion Status' field is blank. The record does not state a completion status.",
    ],
)
def test_neutral_statements_pass(text: str) -> None:
    assert find_allegation_language(text) == []


@pytest.mark.parametrize(
    ("text", "term"),
    [
        ("The developer committed fraud.", "fraud"),
        ("This looks like a kickback scheme.", "kickback"),
        ("The City broke its promise to residents.", "broke its promise"),
        ("Officials MISLED the committee.", "misled"),
    ],
)
def test_allegation_language_is_found(text: str, term: str) -> None:
    assert term in find_allegation_language(text)
