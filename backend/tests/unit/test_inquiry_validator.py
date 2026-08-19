"""validate_inquiry: the deterministic gate between the Inquiry Planner and the ledger."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.schemas.case import BundleEvidence, CaseBundle
from app.schemas.evidence import Evidence
from app.schemas.inquiry import InquiryProposal
from app.services.validator import validate_inquiry
from tests.conftest import FIXTURE_DIR, FIXTURE_EXTRACTION_PATH

CASE_ID = "case-tid121-bronzeville-arts-tech-hub"
AMEND = "tid121-amendment-1-2026"
URL = "https://milwaukee.legistar1.com/milwaukee/attachments/x.pdf"


def _evidence_by_id() -> dict[str, Evidence]:
    payload = json.loads(FIXTURE_EXTRACTION_PATH.read_text())
    return {
        item["evidence_id"]: Evidence.model_validate(item)
        for extraction in payload["extractions"].values()
        for item in extraction["evidence"]
    }


@pytest.fixture(scope="module")
def bundle() -> CaseBundle:
    by_id = _evidence_by_id()
    original = [
        BundleEvidence(evidence=by_id[i], canonical_url=URL, artifact_role="original_commitment")
        for i in by_id
        if i.startswith("ev-tid121-plan")
    ]
    later = [
        BundleEvidence(evidence=by_id[i], canonical_url=URL, artifact_role="later_evidence")
        for i in by_id
        if i.startswith("ev-tid121-amend1")
    ]
    return CaseBundle(
        case_id=CASE_ID,
        case_topic="TID 121",
        trigger_artifact_id=AMEND,
        original_evidence=original,
        later_evidence=later,
        new_evidence_ids=[e.evidence.evidence_id for e in later],
    )


@pytest.fixture(scope="module")
def fixture_inquiry() -> InquiryProposal:
    payload = json.loads((FIXTURE_DIR / "fixture_inquiry.json").read_text())
    return InquiryProposal.model_validate(payload["proposals"][CASE_ID])


def test_fixture_inquiry_passes(fixture_inquiry: InquiryProposal, bundle: CaseBundle) -> None:
    assert validate_inquiry(fixture_inquiry, bundle).ok


def test_schema_forbids_extra_fields(fixture_inquiry: InquiryProposal) -> None:
    payload = fixture_inquiry.model_dump() | {"send_to": "alderman@example.gov"}
    with pytest.raises(ValidationError):
        InquiryProposal.model_validate(payload)


def test_empty_question_refused(fixture_inquiry: InquiryProposal, bundle: CaseBundle) -> None:
    empty = fixture_inquiry.model_copy(update={"proposed_question": "   "})
    result = validate_inquiry(empty, bundle)
    assert not result.ok
    assert any("empty" in reason for reason in result.reasons)


def test_approval_not_required_refused(
    fixture_inquiry: InquiryProposal, bundle: CaseBundle
) -> None:
    sneaky = fixture_inquiry.model_copy(update={"approval_required": False})
    result = validate_inquiry(sneaky, bundle)
    assert not result.ok
    assert any("approval_required" in reason for reason in result.reasons)


def test_allegation_word_in_question_refused(
    fixture_inquiry: InquiryProposal, bundle: CaseBundle
) -> None:
    accusatory = fixture_inquiry.model_copy(
        update={"proposed_question": "Why did the City cover up the missing 2025 report?"}
    )
    result = validate_inquiry(accusatory, bundle)
    assert not result.ok
    assert any("cover-up" in reason or "cover up" in reason for reason in result.reasons)


def test_causal_word_in_rationale_refused(
    fixture_inquiry: InquiryProposal, bundle: CaseBundle
) -> None:
    causal = fixture_inquiry.model_copy(
        update={"scope_rationale": "The City failed to publish the expected report."}
    )
    result = validate_inquiry(causal, bundle)
    assert not result.ok
    assert any("failed to" in reason for reason in result.reasons)


def test_foreign_evidence_id_refused(
    fixture_inquiry: InquiryProposal, bundle: CaseBundle
) -> None:
    foreign = fixture_inquiry.model_copy(
        update={"supporting_evidence_ids": ["ev-tid121-plan-capital-costs", "ev-made-up"]}
    )
    result = validate_inquiry(foreign, bundle)
    assert not result.ok
    assert any("ev-made-up" in reason for reason in result.reasons)


def test_no_supporting_evidence_refused(
    fixture_inquiry: InquiryProposal, bundle: CaseBundle
) -> None:
    unanchored = fixture_inquiry.model_copy(update={"supporting_evidence_ids": []})
    result = validate_inquiry(unanchored, bundle)
    assert not result.ok


def test_student_scope_in_question_refused(
    fixture_inquiry: InquiryProposal, bundle: CaseBundle
) -> None:
    out_of_scope = fixture_inquiry.model_copy(
        update={"proposed_question": "How many students had low attendance near TID 121?"}
    )
    result = validate_inquiry(out_of_scope, bundle)
    assert not result.ok
    assert any("students" in reason or "attendance" in reason for reason in result.reasons)


def test_personnel_scope_in_question_refused(
    fixture_inquiry: InquiryProposal, bundle: CaseBundle
) -> None:
    out_of_scope = fixture_inquiry.model_copy(
        update={"proposed_question": "Provide the personnel file of the DCD project manager."}
    )
    result = validate_inquiry(out_of_scope, bundle)
    assert not result.ok


def test_scope_words_allowed_in_excluded_requests(
    fixture_inquiry: InquiryProposal, bundle: CaseBundle
) -> None:
    """excluded_requests is where the planner promises NOT to ask; scope words belong there."""
    assert "No student-level information." in fixture_inquiry.excluded_requests
    assert validate_inquiry(fixture_inquiry, bundle).ok
