"""Run the reviewed corpus through the City workflow end to end, on a laptop, with no model."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from app.agents.document_evidence import DocumentEvidenceAgentService
from app.agents.factory import GoogleAdkStructuredRunner, StructuredAgentRunner
from app.agents.fake_runner import FakeAgentRunner
from app.agents.routing_runner import RoleRoutingRunner
from app.agents.usage_log import UsageLog
from app.core.config import apply_vertex_env, require_vertex_config
from app.domain.enums import JobStatus, LedgerEventType
from app.orchestration.idempotency import SourceJobKeys
from app.orchestration.routes import CityRouteRegistry
from app.orchestration.workflow import CityDocumentWorkflow, WorkflowResult
from app.policies.policy_service import CivicTracePolicyService
from app.policies.source_policy import SourcePolicy
from app.repositories.cases import InMemoryLedger, LedgerRecorder
from app.repositories.jobs import InMemoryJobRepository
from app.schemas.corpus import CorpusManifest
from app.services.artifact_vault import LocalFixtureVault
from app.services.corpus import load_corpus_manifest
from app.tools.artifact_tools import ArtifactPageReader

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
    delta_path: Path | None = None
    review_path: Path | None = None
    inquiry_path: Path | None = None
    out_path: Path | None = None
    replay_duplicate: bool = False
    runner_kind: str = "fake"  # "fake" (fixtures, default) or "adk" (real Gemini Flash, needs ADC)


@dataclass(frozen=True)
class ReplayResult:
    artifact_id: str
    status: JobStatus
    reason: str | None
    job_key: str


@dataclass
class ReplayReport:
    manifest: CorpusManifest
    ledger: LedgerRecorder
    results: list[ReplayResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(result.status in OK_STATUSES for result in self.results)

    def case_outcome_line(self) -> str:
        """One plain line: did the case end staged, in human review, or with no delta?"""
        events = self.ledger.events()
        staged = [e for e in events if e.event_type is LedgerEventType.DELTA_STAGED]
        human = [e for e in events if e.event_type is LedgerEventType.CASE_HUMAN_REVIEW]
        if staged and staged[-1].delta and staged[-1].review:
            delta, review = staged[-1].delta, staged[-1].review
            inquiries = [e for e in events if e.event_type is LedgerEventType.INQUIRY_STAGED]
            inquiry_note = "  inquiry: STAGED" if inquiries else ""
            return (
                f"{self.manifest.case_id}  DELTA_STAGED ({delta.category})"
                f"  reviewer={review.outcome}  next: {delta.next_evidence_needed}{inquiry_note}"
            )
        if human and human[-1].delta:
            category = human[-1].delta.category
            return f"{self.manifest.case_id}  HUMAN_REVIEW ({category})  {human[-1].reason}"
        return f"{self.manifest.case_id}  NO_DELTA"


def build_workflow(
    manifest: CorpusManifest,
    options: ReplayOptions,
    *,
    clock: Callable[[], datetime],
    ledger: LedgerRecorder | None = None,
) -> tuple[CityDocumentWorkflow, LedgerRecorder, UsageLog | None]:
    """`ledger` defaults to in-memory; the cloud worker injects a FirestoreLedger (MOO-708)."""
    ledger = ledger or InMemoryLedger(
        case_id=manifest.case_id,
        case_topic=manifest.case_topic,
        original_artifact_ids=frozenset(
            entry.artifact_id for entry in manifest.artifacts if entry.role == "original_commitment"
        ),
        clock=clock,
    )
    delta_path = options.delta_path or options.extraction_path.with_name("fixture_delta.json")
    review_path = options.review_path or options.extraction_path.with_name("fixture_review.json")
    inquiry_path = options.inquiry_path or options.extraction_path.with_name(
        "fixture_inquiry.json"
    )
    fake_runner = FakeAgentRunner.from_paths(
        extraction_path=options.extraction_path,
        delta_path=delta_path if delta_path.exists() else None,
        review_path=review_path if review_path.exists() else None,
        inquiry_path=inquiry_path if inquiry_path.exists() else None,
    )
    runner, usage_log = _build_runner(manifest, options, fake_runner)
    hint_pages = {
        entry.artifact_id: [anchor.page for anchor in entry.required_anchors]
        for entry in manifest.artifacts
    }
    workflow = CityDocumentWorkflow(
        artifacts=LocalFixtureVault(
            manifest=manifest, fixture_root=options.fixture_root, vault_dir=options.vault_dir
        ),
        jobs=InMemoryJobRepository(),
        cases=ledger,
        policy=CivicTracePolicyService(
            source_policy=SourcePolicy.from_yaml(options.allowlist_path)
        ),
        agents=DocumentEvidenceAgentService(
            runner, case_id=manifest.case_id, hint_pages=hint_pages
        ),
        routes=CityRouteRegistry(),
        idempotency=SourceJobKeys(),
    )
    return workflow, ledger, usage_log


def _build_runner(
    manifest: CorpusManifest, options: ReplayOptions, fake_runner: FakeAgentRunner
) -> tuple[StructuredAgentRunner, UsageLog | None]:
    if options.runner_kind == "fake":
        return fake_runner, None
    if options.runner_kind != "adk":
        raise ValueError(f"unknown runner kind {options.runner_kind!r}; use 'fake' or 'adk'")
    config = require_vertex_config()
    apply_vertex_env(config)
    usage_log = UsageLog()
    fixture_dir = options.fixture_root / manifest.fixture_dir

    def page_reader_for(artifact_id: str) -> ArtifactPageReader:
        entry = manifest.entry(artifact_id)
        if entry.local_path is None:
            raise ValueError(f"{artifact_id}: no vaulted file to read")
        return ArtifactPageReader(artifact_id=artifact_id, pdf_path=fixture_dir / entry.local_path)

    adk_runner = GoogleAdkStructuredRunner(
        model=config.model,
        page_reader_factory=page_reader_for,
        usage_log=usage_log,
    )
    # Real model for document evidence only; delta + reviewer stay on fixtures until 2.3/2.4.
    return RoleRoutingRunner({"document_evidence": adk_runner}, default=fake_runner), usage_log


def replay_corpus(
    options: ReplayOptions, *, clock: Callable[[], datetime] = lambda: datetime.now(UTC)
) -> ReplayReport:
    manifest = load_corpus_manifest(options.manifest_path)
    workflow, ledger, usage_log = build_workflow(manifest, options, clock=clock)
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
        if usage_log is not None:
            usage_log.write_jsonl(options.out_path.with_name("usage.jsonl"))
    return report


def write_ledger_json(report: ReplayReport, path: Path) -> None:
    payload = {
        "case_id": report.manifest.case_id,
        "case_topic": report.manifest.case_topic,
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
