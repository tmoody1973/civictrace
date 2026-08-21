"""MOO-719: a rejected extraction gets ONE corrected attempt with the validator's reasons.

Models propose; code validates; a rejection feeds back exactly once. A second failure is
recorded as EXTRACTION_REJECTED like before — the gate never loosens.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

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
from app.services.validator import ValidationResult
from tests.conftest import MANIFEST_PATH, REPO_ROOT

PLAN_ID = "tid121-project-plan-2024"
FIXED_NOW = datetime(2026, 8, 21, 14, 0, tzinfo=UTC)


class RetryRecordingAgents:
    def __init__(self, extraction: DocumentExtraction) -> None:
        self._extraction = extraction
        self.revision_notes_seen: list[list[str] | None] = []

    async def document_evidence(
        self,
        artifact: Artifact,
        *,
        context: WorkflowContext,
        revision_notes: list[str] | None = None,
    ) -> DocumentExtraction:
        self.revision_notes_seen.append(revision_notes)
        return self._extraction

    async def entity_resolution(self, extraction, *, context):  # noqa: ANN001, ANN202
        return EntityLinkBatch(links=[])

    async def case_linker(self, extraction, entity_links, case_summaries, *, context):  # noqa: ANN001, ANN202
        return [
            CaseLinkProposal(
                case_id=None, linked_evidence_ids=[], link_status="CANDIDATE", rationale="n/a"
            )
        ]


class RejectNTimesPolicy:
    """Rejects the first `fail_times` validations with a named reason, then passes."""

    def __init__(self, fail_times: int) -> None:
        self._remaining = fail_times

    def assert_source_event_allowed(self, event: SourceEvent) -> None: ...
    def validate_artifact(self, artifact: Artifact) -> None: ...

    def validate_document_extraction(self, extraction, artifact):  # noqa: ANN001, ANN202
        if self._remaining > 0:
            self._remaining -= 1
            return ValidationResult(("ev-1: quoted words not found on page 6",))
        return ValidationResult()

    def validate_entity_links(self, links, extraction) -> None: ...  # noqa: ANN001
    def validate_case_link(self, proposal) -> None: ...  # noqa: ANN001


class DocumentRoutes:
    def requires_document_extraction(self, artifact: Artifact) -> bool:
        return True

    def requires_media_extraction(self, artifact: Artifact) -> bool:
        return False

    def is_unavailable(self, artifact: Artifact) -> bool:
        return False


def _run(tmp_path: Path, fail_times: int, extraction: DocumentExtraction):
    manifest: CorpusManifest = load_corpus_manifest(MANIFEST_PATH)
    agents = RetryRecordingAgents(extraction)
    ledger = InMemoryLedger(
        case_id=manifest.case_id,
        clock=lambda: FIXED_NOW,
        original_artifact_ids=frozenset({PLAN_ID}),
    )
    workflow = CityDocumentWorkflow(
        artifacts=LocalFixtureVault(manifest=manifest, fixture_root=REPO_ROOT, vault_dir=tmp_path),
        jobs=InMemoryJobRepository(),
        cases=ledger,
        policy=RejectNTimesPolicy(fail_times),
        agents=agents,
        routes=DocumentRoutes(),
        idempotency=SourceJobKeys(),
    )
    result = asyncio.run(workflow.run(manifest.source_event(PLAN_ID), trace_id="retry-test"))
    return result, agents, ledger


def test_one_rejection_feeds_back_and_the_corrected_attempt_is_accepted(
    tmp_path: Path, fixture_extraction_payload: dict
) -> None:
    extraction = DocumentExtraction.model_validate(
        fixture_extraction_payload["extractions"][PLAN_ID]
    )
    result, agents, ledger = _run(tmp_path, fail_times=1, extraction=extraction)
    assert result.status is JobStatus.SUCCEEDED
    assert agents.revision_notes_seen == [None, ["ev-1: quoted words not found on page 6"]]
    accepted = [e for e in ledger.events() if e.event_type is LedgerEventType.EVIDENCE_ACCEPTED]
    assert len(accepted) == len(extraction.evidence)


def test_a_second_failure_is_rejected_for_good(
    tmp_path: Path, fixture_extraction_payload: dict
) -> None:
    extraction = DocumentExtraction.model_validate(
        fixture_extraction_payload["extractions"][PLAN_ID]
    )
    result, agents, ledger = _run(tmp_path, fail_times=2, extraction=extraction)
    assert result.status is JobStatus.EXTRACTION_REJECTED
    assert len(agents.revision_notes_seen) == 2, "exactly one retry, never a loop"
    rejected = [e for e in ledger.events() if e.event_type is LedgerEventType.EXTRACTION_REJECTED]
    assert len(rejected) == 1
