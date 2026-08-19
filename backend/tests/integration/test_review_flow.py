"""Proposed delta → Quality Reviewer (fake) → only APPROVE with zero issues stages the delta."""

from __future__ import annotations

import asyncio
import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.enums import JobStatus, LedgerEventType, ReviewOutcome
from app.schemas.case import BlockingIssue, DecisionDeltaProposal, ReviewDecision
from app.services.corpus import load_corpus_manifest
from app.services.replay import ReplayOptions, build_workflow
from tests.conftest import ALLOWLIST_PATH, FIXTURE_DIR, MANIFEST_PATH, REPO_ROOT

NOW = datetime(2026, 8, 19, 18, 0, tzinfo=UTC)
PLAN, AMEND = "tid121-project-plan-2024", "tid121-amendment-1-2026"
CASE_ID = "case-tid121-bronzeville-arts-tech-hub"


def _options(tmp_path: Path, review_path: Path | None = None) -> ReplayOptions:
    return ReplayOptions(
        manifest_path=MANIFEST_PATH,
        allowlist_path=ALLOWLIST_PATH,
        extraction_path=FIXTURE_DIR / "fixture_extraction.json",
        fixture_root=REPO_ROOT,
        vault_dir=tmp_path / "vault",
        review_path=review_path,
    )


def _run(tmp_path: Path, review_path: Path | None = None):
    manifest = load_corpus_manifest(MANIFEST_PATH)
    workflow, ledger, _ = build_workflow(
        manifest, _options(tmp_path, review_path), clock=lambda: NOW
    )
    results = [
        asyncio.run(workflow.run(manifest.source_event(a), trace_id=f"t-{i}"))
        for i, a in enumerate([PLAN, AMEND])
    ]
    return results, ledger


def _of(ledger, kind: LedgerEventType):  # noqa: ANN001, ANN202
    return [e for e in ledger.events() if e.event_type is kind]


def test_approved_review_stages_the_delta(tmp_path: Path) -> None:
    results, ledger = _run(tmp_path)
    assert results[1].status is JobStatus.SUCCEEDED
    assert results[1].staged_case_ids == (CASE_ID,)
    assert len(_of(ledger, LedgerEventType.DELTA_PROPOSED)) == 1
    staged = _of(ledger, LedgerEventType.DELTA_STAGED)
    assert len(staged) == 1
    assert staged[0].review is not None and staged[0].review.outcome is ReviewOutcome.APPROVE
    assert staged[0].review.notes and "Both sides anchored" in staged[0].review.notes[0]
    assert staged[0].delta is not None and staged[0].delta.requires_human_review is True
    assert _of(ledger, LedgerEventType.CASE_HUMAN_REVIEW) == []
    # order in the log: proposed before staged
    kinds = [e.event_type for e in ledger.events()]
    assert kinds.index(LedgerEventType.DELTA_PROPOSED) < kinds.index(LedgerEventType.DELTA_STAGED)


def test_rejected_review_lands_in_human_review(tmp_path: Path) -> None:
    payload = json.loads((FIXTURE_DIR / "fixture_review.json").read_text())
    tampered = copy.deepcopy(payload)
    tampered["reviews"][AMEND] = {
        "outcome": "REJECT",
        "blocking_issues": [
            {
                "code": "MISSING_LATER_ANCHOR",
                "field": "later_evidence_ids",
                "fix": "Provide one later evidence anchor or downgrade to NO_MATERIAL_DELTA.",
            }
        ],
        "notes": [],
        "policy_flags": [],
        "review_summary": "Rejected for test.",
    }
    review_path = tmp_path / "fixture_review.json"
    review_path.write_text(json.dumps(tampered))
    results, ledger = _run(tmp_path, review_path)
    assert results[1].staged_case_ids == ()
    assert _of(ledger, LedgerEventType.DELTA_STAGED) == []
    human = _of(ledger, LedgerEventType.CASE_HUMAN_REVIEW)
    assert len(human) == 1
    assert human[0].reason and "MISSING_LATER_ANCHOR" in human[0].reason
    assert human[0].review is not None and human[0].review.outcome is ReviewOutcome.REJECT


def test_rerun_adds_no_review_events(tmp_path: Path) -> None:
    manifest = load_corpus_manifest(MANIFEST_PATH)
    workflow, ledger, _ = build_workflow(manifest, _options(tmp_path), clock=lambda: NOW)
    for a in [PLAN, AMEND]:
        asyncio.run(workflow.run(manifest.source_event(a), trace_id="t"))
    before = len(ledger.events())
    asyncio.run(workflow.run(manifest.source_event(AMEND), trace_id="t2"))
    assert len(ledger.events()) == before


def test_approve_with_blocking_issues_is_not_stageable() -> None:
    from app.policies.policy_service import CivicTracePolicyService
    from app.policies.source_policy import SourcePolicy

    policy = CivicTracePolicyService(source_policy=SourcePolicy.from_yaml(ALLOWLIST_PATH))
    delta_payload = json.loads((FIXTURE_DIR / "fixture_delta.json").read_text())["proposals"][AMEND]
    delta = DecisionDeltaProposal.model_validate(delta_payload)
    sneaky = ReviewDecision(
        outcome=ReviewOutcome.APPROVE,
        blocking_issues=[BlockingIssue(code="X", field="neutral_summary", fix="rewrite")],
    )
    assert policy.review_is_stageable(sneaky, delta) is False
    clean = ReviewDecision(outcome=ReviewOutcome.APPROVE)
    assert policy.review_is_stageable(clean, delta) is True
    no_human = delta.model_copy(update={"requires_human_review": False})
    assert policy.review_is_stageable(clean, no_human) is False


@pytest.mark.parametrize("outcome", ["REVISE", "REJECT", "HUMAN_REVIEW"])
def test_non_approve_outcomes_never_stage(outcome: str) -> None:
    from app.policies.policy_service import CivicTracePolicyService
    from app.policies.source_policy import SourcePolicy

    policy = CivicTracePolicyService(source_policy=SourcePolicy.from_yaml(ALLOWLIST_PATH))
    delta_payload = json.loads((FIXTURE_DIR / "fixture_delta.json").read_text())["proposals"][AMEND]
    delta = DecisionDeltaProposal.model_validate(delta_payload)
    assert (
        policy.review_is_stageable(ReviewDecision(outcome=ReviewOutcome(outcome)), delta) is False
    )
