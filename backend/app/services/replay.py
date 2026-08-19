"""Run the reviewed corpus through the City workflow end to end, on a laptop, with no model."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.agents.document_evidence import DocumentEvidenceAgentService
from app.agents.fake_runner import FakeAgentRunner
from app.domain.enums import JobStatus
from app.orchestration.idempotency import SourceJobKeys
from app.orchestration.routes import CityRouteRegistry
from app.orchestration.workflow import CityDocumentWorkflow, WorkflowResult
from app.policies.policy_service import CivicTracePolicyService
from app.policies.source_policy import SourcePolicy
from app.repositories.cases import InMemoryLedger
from app.repositories.jobs import InMemoryJobRepository
from app.schemas.corpus import CorpusManifest
from app.services.artifact_vault import LocalFixtureVault
from app.services.corpus import load_corpus_manifest

OK_STATUSES = frozenset(
    {JobStatus.SUCCEEDED, JobStatus.DUPLICATE_SUPPRESSED, JobStatus.NOT_PUBLISHED}
)


@dataclass(frozen=True)
class ReplayOptions:
    manifest_path: Path
    allowlist_path: Path
    extraction_path: Path
    fixture_root: Path
    vault_dir: Path
    out_path: Path | None = None
    replay_duplicate: bool = False


@dataclass(frozen=True)
class ReplayResult:
    artifact_id: str
    status: JobStatus
    reason: str | None
    job_key: str


@dataclass
class ReplayReport:
    manifest: CorpusManifest
    ledger: InMemoryLedger
    results: list[ReplayResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(result.status in OK_STATUSES for result in self.results)


def build_workflow(
    manifest: CorpusManifest, options: ReplayOptions, *, clock: Callable[[], datetime]
) -> tuple[CityDocumentWorkflow, InMemoryLedger]:
    ledger = InMemoryLedger(case_id=manifest.case_id, clock=clock)
    workflow = CityDocumentWorkflow(
        artifacts=LocalFixtureVault(
            manifest=manifest, fixture_root=options.fixture_root, vault_dir=options.vault_dir
        ),
        jobs=InMemoryJobRepository(),
        cases=ledger,
        policy=CivicTracePolicyService(
            source_policy=SourcePolicy.from_yaml(options.allowlist_path)
        ),
        agents=DocumentEvidenceAgentService(FakeAgentRunner.from_path(options.extraction_path)),
        routes=CityRouteRegistry(),
        idempotency=SourceJobKeys(),
    )
    return workflow, ledger


def replay_corpus(
    options: ReplayOptions, *, clock: Callable[[], datetime] = lambda: datetime.now(UTC)
) -> ReplayReport:
    manifest = load_corpus_manifest(options.manifest_path)
    workflow, ledger = build_workflow(manifest, options, clock=clock)
    report = ReplayReport(manifest=manifest, ledger=ledger)
    artifact_ids = [entry.artifact_id for entry in manifest.artifacts]
    if options.replay_duplicate:
        artifact_ids.append(manifest.duplicate_event_fixture.artifact_id)
    for index, artifact_id in enumerate(artifact_ids):
        outcome = asyncio.run(
            workflow.run(manifest.source_event(artifact_id), trace_id=f"replay-{index}")
        )
        report.results.append(_to_result(artifact_id, outcome))
    if options.out_path is not None:
        write_ledger_json(report, options.out_path)
    return report


def write_ledger_json(report: ReplayReport, path: Path) -> None:
    payload = {
        "case_id": report.manifest.case_id,
        "corpus_id": report.manifest.corpus_id,
        "events": [event.model_dump(mode="json") for event in report.ledger.events()],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _to_result(artifact_id: str, outcome: WorkflowResult) -> ReplayResult:
    return ReplayResult(
        artifact_id=artifact_id,
        status=outcome.status,
        reason=outcome.reason,
        job_key=outcome.job_key,
    )
