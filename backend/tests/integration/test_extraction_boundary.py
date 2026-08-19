"""Fixture event → vault → route → FakeAgentRunner → validator → ledger. Four outcomes, no model."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.agents.document_evidence import DocumentEvidenceAgentService
from app.agents.fake_runner import FakeAgentRunner
from app.domain.enums import JobStatus, LedgerEventType
from app.orchestration.idempotency import SourceJobKeys
from app.orchestration.routes import CityRouteRegistry
from app.orchestration.workflow import CityDocumentWorkflow
from app.policies.policy_service import CivicTracePolicyService
from app.policies.source_policy import SourcePolicy
from app.repositories.cases import InMemoryLedger
from app.repositories.jobs import InMemoryJobRepository
from app.schemas.corpus import CorpusManifest
from app.services.artifact_vault import LocalFixtureVault
from app.services.corpus import load_corpus_manifest
from tests.conftest import (
    ALLOWLIST_PATH,
    FIXTURE_DIR,
    FIXTURE_EXTRACTION_PATH,
    MANIFEST_PATH,
    REPO_ROOT,
)

PLAN_ID = "tid121-project-plan-2024"
MISSING_ID = "tid-annual-report-2025"
NOW = datetime(2026, 8, 19, 15, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def manifest() -> CorpusManifest:
    return load_corpus_manifest(MANIFEST_PATH)


def _build(manifest: CorpusManifest, tmp_path: Path, extraction_payload: dict | None = None):
    runner = (
        FakeAgentRunner.from_paths(
            extraction_path=FIXTURE_EXTRACTION_PATH,
            delta_path=FIXTURE_DIR / "fixture_delta.json",
            review_path=FIXTURE_DIR / "fixture_review.json",
            inquiry_path=FIXTURE_DIR / "fixture_inquiry.json",
        )
        if extraction_payload is None
        else FakeAgentRunner.from_payloads(extraction=extraction_payload)
    )
    ledger = InMemoryLedger(
        case_id=manifest.case_id, clock=lambda: NOW, original_artifact_ids=frozenset({PLAN_ID})
    )
    workflow = CityDocumentWorkflow(
        artifacts=LocalFixtureVault(manifest=manifest, fixture_root=REPO_ROOT, vault_dir=tmp_path),
        jobs=InMemoryJobRepository(),
        cases=ledger,
        policy=CivicTracePolicyService(source_policy=SourcePolicy.from_yaml(ALLOWLIST_PATH)),
        agents=DocumentEvidenceAgentService(runner, case_id=manifest.case_id),
        routes=CityRouteRegistry(),
        idempotency=SourceJobKeys(),
    )
    return workflow, runner, ledger


def _events(ledger: InMemoryLedger, kind: LedgerEventType):
    return [event for event in ledger.events() if event.event_type is kind]


def test_valid_fixture_yields_anchored_evidence_for_every_artifact(
    manifest: CorpusManifest, tmp_path: Path
) -> None:
    workflow, runner, ledger = _build(manifest, tmp_path)
    for entry in manifest.artifacts:
        if entry.artifact_id == MISSING_ID:
            continue
        result = asyncio.run(workflow.run(manifest.source_event(entry.artifact_id), trace_id="t"))
        assert result.status is JobStatus.SUCCEEDED, result
    accepted = _events(ledger, LedgerEventType.EVIDENCE_ACCEPTED)
    assert len(accepted) == 8
    assert _events(ledger, LedgerEventType.EXTRACTION_REJECTED) == []
    required = {
        (entry.artifact_id, str(anchor.page))
        for entry in manifest.artifacts
        for anchor in entry.required_anchors
    }
    anchored = {
        (event.evidence.artifact_id, anchor.anchor_value)
        for event in accepted
        if event.evidence
        for anchor in event.evidence.anchors
    }
    assert required <= anchored, required - anchored
    evidence_calls = [c for c in runner.calls if c.agent_name == "civictrace-document_evidence"]
    assert len(evidence_calls) == 3


def test_missing_record_is_not_published_and_agent_is_never_called(
    manifest: CorpusManifest, tmp_path: Path
) -> None:
    workflow, runner, ledger = _build(manifest, tmp_path)
    result = asyncio.run(workflow.run(manifest.source_event(MISSING_ID), trace_id="t"))
    assert result.status is JobStatus.NOT_PUBLISHED
    assert result.reason and "2025" in result.reason
    events = ledger.events()
    assert len(events) == 1 and events[0].event_type is LedgerEventType.ARTIFACT_NOT_PUBLISHED
    assert events[0].artifact and events[0].artifact.content_hash is None
    assert runner.calls == []


def _tamper(payload: dict, mutate) -> dict:  # noqa: ANN001
    import copy

    tampered = copy.deepcopy(payload)
    mutate(tampered["extractions"][PLAN_ID])
    return tampered


@pytest.mark.parametrize(
    ("label", "mutate"),
    [
        ("anchor removed", lambda ex: ex["evidence"][0].__setitem__("anchors", [])),
        (
            "fake quote",
            lambda ex: ex["evidence"][1].__setitem__(
                "verbatim_excerpt", "TOTAL Capital Project Costs $9,700,000"
            ),
        ),
        (
            "fake artifact id",
            lambda ex: ex["evidence"][0]["anchors"][0].__setitem__("artifact_id", "some-other-pdf"),
        ),
        ("wrong page", lambda ex: ex["evidence"][1]["anchors"][0].__setitem__("anchor_value", "9")),
        (
            "pii in excerpt",
            lambda ex: ex["evidence"][0].__setitem__("verbatim_excerpt", "call 414-555-0199"),
        ),
    ],
)
def test_tampered_extraction_is_rejected_as_a_ledger_event(
    manifest: CorpusManifest, tmp_path: Path, fixture_extraction_payload: dict, label: str, mutate
) -> None:  # noqa: ANN001
    workflow, runner, ledger = _build(
        manifest, tmp_path, _tamper(fixture_extraction_payload, mutate)
    )
    result = asyncio.run(workflow.run(manifest.source_event(PLAN_ID), trace_id="t"))
    assert result.status is JobStatus.EXTRACTION_REJECTED, label
    assert _events(ledger, LedgerEventType.EVIDENCE_ACCEPTED) == [], label
    rejected = _events(ledger, LedgerEventType.EXTRACTION_REJECTED)
    assert len(rejected) == 1 and rejected[0].reason, label
