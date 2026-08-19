"""Deterministic validators: evidence before prose, and no one-sided Decision Delta."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.enums import ArtifactAvailability, DeltaCategory
from app.schemas.case import DecisionDelta
from app.schemas.evidence import DocumentExtraction
from app.schemas.source import Artifact
from app.services.validator import validate_delta, validate_extraction

PLAN_ID = "tid121-project-plan-2024"


@pytest.fixture
def plan_artifact() -> Artifact:
    return Artifact(
        artifact_id=PLAN_ID,
        source_id="milwaukee_legistar",
        canonical_url="https://milwaukee.legistar1.com/milwaukee/attachments/5fe0f830.pdf",
        external_id="240382/attachment/223678",
        title="Project Plan - Bronzeville Arts and Tech Hub",
        media_type="application/pdf",
        content_hash="sha256:7097a1ba6af1fc2aaa60a1d3e9a2b366d63ab067a8e6b4e052b46e8400aaefe1",
        byte_length=2728839,
        page_count=31,
        storage_uri="file:///vault/tid121-project-plan-2024.pdf",
        retrieved_at=datetime(2026, 8, 19, 13, 35, tzinfo=UTC),
        availability=ArtifactAvailability.AVAILABLE,
    )


@pytest.fixture
def plan_extraction(fixture_extraction_payload: dict) -> DocumentExtraction:
    return DocumentExtraction.model_validate(fixture_extraction_payload["extractions"][PLAN_ID])


def test_fixture_extraction_passes(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact
) -> None:
    result = validate_extraction(plan_extraction, plan_artifact)
    assert result.ok, result.reasons


def test_anchorless_evidence_is_rejected(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact
) -> None:
    stripped = plan_extraction.model_copy(
        update={"evidence": [plan_extraction.evidence[0].model_copy(update={"anchors": []})]}
    )
    result = validate_extraction(stripped, plan_artifact)
    assert not result.ok
    assert any("no anchor" in reason for reason in result.reasons)


def test_anchor_to_unknown_artifact_is_rejected(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact
) -> None:
    item = plan_extraction.evidence[0]
    foreign_anchor = item.anchors[0].model_copy(update={"artifact_id": "someone-elses-pdf"})
    tampered = plan_extraction.model_copy(
        update={"evidence": [item.model_copy(update={"anchors": [foreign_anchor]})]}
    )
    result = validate_extraction(tampered, plan_artifact)
    assert not result.ok
    assert any("unknown artifact" in reason for reason in result.reasons)


def test_extraction_for_other_artifact_is_rejected(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact
) -> None:
    other = plan_artifact.model_copy(update={"artifact_id": "tid121-amendment-1-2026"})
    result = validate_extraction(plan_extraction, other)
    assert not result.ok


def test_page_anchor_beyond_page_count_is_rejected(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact
) -> None:
    item = plan_extraction.evidence[0]
    far_anchor = item.anchors[0].model_copy(update={"anchor_value": "999"})
    tampered = plan_extraction.model_copy(
        update={"evidence": [item.model_copy(update={"anchors": [far_anchor]})]}
    )
    result = validate_extraction(tampered, plan_artifact)
    assert not result.ok
    assert any("page 999" in reason for reason in result.reasons)


def test_unpublished_artifact_cannot_carry_evidence(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact
) -> None:
    missing = Artifact(
        artifact_id=PLAN_ID,
        source_id="milwaukee_legistar",
        canonical_url=None,
        external_id="expected:annual-tid-report-2025",
        title=None,
        media_type=None,
        content_hash=None,
        byte_length=None,
        page_count=None,
        storage_uri=None,
        retrieved_at=datetime(2026, 8, 19, tzinfo=UTC),
        availability=ArtifactAvailability.NOT_PUBLISHED,
        availability_reason="No 2025 annual report in Legistar as of 2026-08-19.",
    )
    result = validate_extraction(plan_extraction, missing)
    assert not result.ok
    assert any("NOT_PUBLISHED" in reason for reason in result.reasons)


def _delta(original: list[str], later: list[str]) -> DecisionDelta:
    return DecisionDelta(
        case_id="case-tid121-bronzeville-arts-tech-hub",
        category=DeltaCategory.REVISED,
        neutral_summary="The 2026 amendment revises the TID capital costs in the 2024 plan.",
        original_evidence_ids=original,
        later_evidence_ids=later,
        what_is_established=["Plan p.5: $700,000; Amendment p.3: $2,345,000."],
        what_is_not_established=["Why the amendment was needed."],
        next_evidence_needed="2025 Annual TID Report",
    )


def test_delta_with_both_sides_passes() -> None:
    assert validate_delta(_delta(["ev-plan"], ["ev-amend"])).ok


@pytest.mark.parametrize(("original", "later"), [([], ["ev-amend"]), (["ev-plan"], []), ([], [])])
def test_one_sided_delta_is_rejected(original: list[str], later: list[str]) -> None:
    result = validate_delta(_delta(original, later))
    assert not result.ok


def test_delta_defaults_to_human_review() -> None:
    assert _delta(["ev-plan"], ["ev-amend"]).requires_human_review is True


@pytest.mark.parametrize("bad_page", ["0", "abc", "-3", ""])
def test_non_page_anchor_values_are_rejected(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact, bad_page: str
) -> None:
    item = plan_extraction.evidence[0]
    bad_anchor = item.anchors[0].model_copy(update={"anchor_value": bad_page})
    tampered = plan_extraction.model_copy(
        update={"evidence": [item.model_copy(update={"anchors": [bad_anchor]})]}
    )
    result = validate_extraction(tampered, plan_artifact)
    assert not result.ok
    assert any("outside 1..31" in reason for reason in result.reasons)


def test_allegation_language_in_neutral_statement_is_rejected(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact
) -> None:
    item = plan_extraction.evidence[1]
    accusing = item.model_copy(
        update={"neutral_statement": "The City's $700,000 grant was a kickback."}
    )
    tampered = plan_extraction.model_copy(update={"evidence": [accusing]})
    result = validate_extraction(tampered, plan_artifact)
    assert not result.ok
    assert any("allegation language" in reason for reason in result.reasons)


def test_allegation_words_inside_the_verbatim_quote_are_not_filtered(
    plan_extraction: DocumentExtraction, plan_artifact: Artifact
) -> None:
    # The public record may itself say "fraud" (e.g. a statute title); quoting it is fine.
    item = plan_extraction.evidence[1]
    quoting = item.model_copy(update={"verbatim_excerpt": "TOTAL Capital Project Costs $700,000"})
    assert validate_extraction(
        plan_extraction.model_copy(update={"evidence": [quoting]}), plan_artifact
    ).ok
    quoting_fraud_word = item.model_copy(update={"verbatim_excerpt": "anti-fraud provisions"})
    result = validate_extraction(
        plan_extraction.model_copy(update={"evidence": [quoting_fraud_word]}), plan_artifact
    )
    assert not any("allegation" in reason for reason in result.reasons)
