"""Run the outline workflow twice with the same event: second run is suppressed, touches nothing."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.enums import JobStatus, LedgerEventType
from app.orchestration.idempotency import SourceJobKeys
from app.orchestration.workflow import CityDocumentWorkflow, WorkflowContext
from app.repositories.cases import InMemoryLedger
from app.repositories.jobs import InMemoryJobRepository
from app.schemas.case import CaseLinkProposal
from app.schemas.corpus import CorpusManifest
from app.schemas.evidence import DocumentExtraction, EntityLinkBatch
from app.schemas.source import Artifact, SourceEvent
from app.services.artifact_vault import LocalFixtureVault
from app.services.corpus import load_corpus_manifest
from tests.conftest import MANIFEST_PATH, REPO_ROOT

PLAN_ID = "tid121-project-plan-2024"
FIXED_NOW = datetime(2026, 8, 19, 14, 0, tzinfo=UTC)


class CountingVault:
    def __init__(self, inner: LocalFixtureVault) -> None:
        self.inner, self.calls = inner, 0

    async def fetch_and_store(self, event: SourceEvent, *, context: WorkflowContext) -> Artifact:
        self.calls += 1
        return await self.inner.fetch_and_store(event, context=context)


class CountingAgents:
    def __init__(self, extraction: DocumentExtraction) -> None:
        self._extraction, self.calls = extraction, 0

    async def document_evidence(
        self, artifact: Artifact, *, context: WorkflowContext
    ) -> DocumentExtraction:
        self.calls += 1
        return self._extraction

    async def entity_resolution(
        self, extraction: DocumentExtraction, *, context: WorkflowContext
    ) -> EntityLinkBatch:
        return EntityLinkBatch(links=[])

    async def case_linker(
        self, extraction, entity_links, case_summaries, *, context
    ) -> list[CaseLinkProposal]:  # noqa: ANN001
        return []

    async def delta_investigator(self, case_bundle, *, context):  # noqa: ANN001, ANN202
        raise AssertionError("not reached in Slice 1")

    async def quality_reviewer(self, delta, case_bundle, *, context):  # noqa: ANN001, ANN202
        raise AssertionError("not reached in Slice 1")


class PermissivePolicy:
    def assert_source_event_allowed(self, event: SourceEvent) -> None: ...
    def validate_artifact(self, artifact: Artifact) -> None: ...
    def validate_document_extraction(self, extraction, artifact) -> None: ...  # noqa: ANN001
    def validate_entity_links(self, links, extraction) -> None: ...  # noqa: ANN001
    def validate_case_link(self, proposal) -> None: ...  # noqa: ANN001
    def validate_delta(self, delta, case_bundle) -> None: ...  # noqa: ANN001
    def assert_review_acceptable(self, review) -> None: ...  # noqa: ANN001


class DocumentRoutes:
    def requires_document_extraction(self, artifact: Artifact) -> bool:
        return True

    def is_unavailable(self, artifact: Artifact) -> bool:
        return False


@pytest.fixture
def manifest() -> CorpusManifest:
    return load_corpus_manifest(MANIFEST_PATH)


def _workflow(manifest: CorpusManifest, tmp_path: Path, extraction: DocumentExtraction):
    vault = CountingVault(
        LocalFixtureVault(manifest=manifest, fixture_root=REPO_ROOT, vault_dir=tmp_path)
    )
    agents = CountingAgents(extraction)
    ledger = InMemoryLedger(case_id=manifest.case_id, clock=lambda: FIXED_NOW)
    workflow = CityDocumentWorkflow(
        artifacts=vault,
        jobs=InMemoryJobRepository(),
        cases=ledger,
        policy=PermissivePolicy(),
        agents=agents,
        routes=DocumentRoutes(),
        idempotency=SourceJobKeys(),
    )
    return workflow, vault, agents, ledger


def test_second_delivery_is_suppressed_and_touches_nothing(
    manifest: CorpusManifest, tmp_path: Path, fixture_extraction_payload: dict
) -> None:
    extraction = DocumentExtraction.model_validate(
        fixture_extraction_payload["extractions"][PLAN_ID]
    )
    workflow, vault, agents, ledger = _workflow(manifest, tmp_path, extraction)
    event = manifest.source_event(PLAN_ID)

    first = asyncio.run(workflow.run(event, trace_id="trace-1"))
    assert first.status is JobStatus.SUCCEEDED
    assert vault.calls == 1 and agents.calls == 1
    accepted = [e for e in ledger.events() if e.event_type is LedgerEventType.EVIDENCE_ACCEPTED]
    assert len(accepted) == len(extraction.evidence) == 3

    second = asyncio.run(workflow.run(event, trace_id="trace-2"))
    assert second.status is JobStatus.DUPLICATE_SUPPRESSED
    assert second.job_key == first.job_key
    assert vault.calls == 1 and agents.calls == 1, "second run must not touch vault or agent"
    assert len(ledger.events()) == 3, "no new ledger events on the duplicate"
