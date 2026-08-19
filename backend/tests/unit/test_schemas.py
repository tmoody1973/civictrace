"""The evidence contracts must load the reviewed fixture exactly and reject anything extra."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.enums import AnchorType, EvidenceStatus
from app.schemas.evidence import DocumentExtraction, Evidence, EvidenceAnchor

FIXTURE_ARTIFACT_IDS = {
    "tid121-project-plan-2024",
    "tid-annual-report-2024",
    "tid121-amendment-1-2026",
}


def test_fixture_extraction_loads_into_document_extraction(
    fixture_extraction_payload: dict,
) -> None:
    extractions = {
        artifact_id: DocumentExtraction.model_validate(raw)
        for artifact_id, raw in fixture_extraction_payload["extractions"].items()
    }
    assert set(extractions) == FIXTURE_ARTIFACT_IDS
    assert sum(len(extraction.evidence) for extraction in extractions.values()) == 8


def test_every_fixture_evidence_item_has_a_page_anchor(fixture_extraction_payload: dict) -> None:
    for raw in fixture_extraction_payload["extractions"].values():
        for item in DocumentExtraction.model_validate(raw).evidence:
            assert item.anchors, item.evidence_id
            assert all(anchor.anchor_type is AnchorType.PAGE for anchor in item.anchors)


def test_blank_completion_status_is_unknown(fixture_extraction_payload: dict) -> None:
    annual = DocumentExtraction.model_validate(
        fixture_extraction_payload["extractions"]["tid-annual-report-2024"]
    )
    by_id = {item.evidence_id: item for item in annual.evidence}
    assert by_id["ev-tid121-annual2024-completion-status"].status is EvidenceStatus.UNKNOWN


def _minimal_evidence(**overrides: object) -> dict:
    base = {
        "evidence_id": "ev-1",
        "artifact_id": "art-1",
        "object_type": "COMMITMENT",
        "verbatim_excerpt": "TOTAL Capital Project Costs $700,000",
        "neutral_statement": "The plan sets total capital project costs at $700,000.",
        "anchors": [{"artifact_id": "art-1", "anchor_type": "page", "anchor_value": "5"}],
        "status": "SUPPORTED",
        "limitations": [],
    }
    return {**base, **overrides}


def test_extra_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Evidence.model_validate(_minimal_evidence(confidence=0.9))


def test_unrecognized_status_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Evidence.model_validate(_minimal_evidence(status="PROBABLY"))


def test_unrecognized_anchor_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        EvidenceAnchor.model_validate(
            {"artifact_id": "art-1", "anchor_type": "vibes", "anchor_value": "1"}
        )
