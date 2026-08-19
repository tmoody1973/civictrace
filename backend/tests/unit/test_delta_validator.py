"""A Decision Delta enters the ledger only with both sides anchored and neutral language."""

from __future__ import annotations

import json

import pytest

from app.domain.enums import DeltaCategory, DeltaResultType, EvidenceStatus, Materiality
from app.schemas.case import BundleEvidence, CaseBundle, DecisionDeltaProposal
from app.schemas.evidence import Evidence
from app.services.validator import validate_delta
from tests.conftest import FIXTURE_DIR, FIXTURE_EXTRACTION_PATH

CASE_ID = "case-tid121-bronzeville-arts-tech-hub"
PLAN = "tid121-project-plan-2024"
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
        not_published_artifact_ids=["tid-annual-report-2025"],
    )


@pytest.fixture(scope="module")
def fixture_delta() -> DecisionDeltaProposal:
    payload = json.loads((FIXTURE_DIR / "fixture_delta.json").read_text())
    return DecisionDeltaProposal.model_validate(payload["proposals"][AMEND])


def test_fixture_delta_passes(fixture_delta: DecisionDeltaProposal, bundle: CaseBundle) -> None:
    result = validate_delta(fixture_delta, bundle)
    assert result.ok, result.reasons
    assert fixture_delta.category is DeltaCategory.REVISED
    assert fixture_delta.result_type is DeltaResultType.DECISION_DELTA
    assert fixture_delta.materiality is Materiality.HIGH


def test_missing_later_side_is_rejected(
    fixture_delta: DecisionDeltaProposal, bundle: CaseBundle
) -> None:
    result = validate_delta(fixture_delta.model_copy(update={"later_evidence_ids": []}), bundle)
    assert not result.ok and any("no later evidence" in r for r in result.reasons)


def test_id_not_in_bundle_is_rejected(
    fixture_delta: DecisionDeltaProposal, bundle: CaseBundle
) -> None:
    tampered = fixture_delta.model_copy(update={"later_evidence_ids": ["ev-made-up"]})
    result = validate_delta(tampered, bundle)
    assert not result.ok and any("ev-made-up" in r and "not in bundle" in r for r in result.reasons)


def test_original_id_on_wrong_side_is_rejected(
    fixture_delta: DecisionDeltaProposal, bundle: CaseBundle
) -> None:
    tampered = fixture_delta.model_copy(
        update={"later_evidence_ids": ["ev-tid121-plan-capital-costs"]}
    )
    result = validate_delta(tampered, bundle)
    assert not result.ok and any("wrong side" in r for r in result.reasons)


def test_causal_language_in_summary_is_rejected(
    fixture_delta: DecisionDeltaProposal, bundle: CaseBundle
) -> None:
    tampered = fixture_delta.model_copy(
        update={
            "neutral_summary": "Costs rose to $2,345,000 because the developer mismanaged funds."
        }
    )
    result = validate_delta(tampered, bundle)
    assert not result.ok and any("causal language" in r for r in result.reasons)


def test_allegation_language_anywhere_is_rejected(
    fixture_delta: DecisionDeltaProposal, bundle: CaseBundle
) -> None:
    tampered = fixture_delta.model_copy(
        update={"what_is_established": ["The grant increase looks like a kickback."]}
    )
    result = validate_delta(tampered, bundle)
    assert not result.ok and any("allegation language" in r for r in result.reasons)


def test_human_review_cannot_be_switched_off(
    fixture_delta: DecisionDeltaProposal, bundle: CaseBundle
) -> None:
    result = validate_delta(
        fixture_delta.model_copy(update={"requires_human_review": False}), bundle
    )
    assert not result.ok and any("requires_human_review" in r for r in result.reasons)


def test_no_material_delta_may_omit_sides_but_ids_must_still_exist(bundle: CaseBundle) -> None:
    payload = json.loads((FIXTURE_DIR / "fixture_delta.json").read_text())
    proposal = DecisionDeltaProposal.model_validate(payload["proposals"]["tid-annual-report-2024"])
    # annual-report ids are not in this amendment-triggered bundle → reject; with empty sides → ok
    assert not validate_delta(proposal, bundle).ok
    empty = proposal.model_copy(update={"original_evidence_ids": [], "later_evidence_ids": []})
    assert validate_delta(empty, bundle).ok


def test_bundle_evidence_status_is_preserved(bundle: CaseBundle) -> None:
    assert all(item.evidence.status in EvidenceStatus for item in bundle.original_evidence)
