"""CivicTrace deterministic City document workflow.

This file intentionally does not expose raw ADK or Google Cloud calls. Those are injected
behind typed protocols so every workflow can be tested with fakes before deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import DeltaResultType, JobStatus
from app.schemas.case import CaseBundle, CaseLinkProposal, DecisionDeltaProposal, ReviewDecision
from app.schemas.evidence import DocumentExtraction, EntityLinkBatch, MediaExtraction
from app.schemas.inquiry import InquiryProposal
from app.schemas.source import Artifact, SourceEvent


@dataclass(frozen=True)
class WorkflowContext:
    trace_id: str
    job_key: str
    actor: str = "system"


@dataclass(frozen=True)
class WorkflowResult:
    status: JobStatus
    job_key: str
    staged_case_ids: tuple[str, ...] = ()
    reason: str | None = None


class ArtifactVault(Protocol):
    async def fetch_and_store(
        self, event: SourceEvent, *, context: WorkflowContext
    ) -> Artifact: ...


class JobRepository(Protocol):
    async def exists_terminal(self, job_key: str) -> bool: ...
    async def start(self, job_key: str, *, context: WorkflowContext) -> None: ...
    async def succeed(self, job_key: str, *, context: WorkflowContext) -> None: ...
    async def fail(self, job_key: str, *, error_code: str, context: WorkflowContext) -> None: ...


class CaseRepository(Protocol):
    async def append_validated_extraction(
        self, extraction: DocumentExtraction, *, context: WorkflowContext
    ) -> None: ...
    async def active_case_summaries(
        self, *, candidate_entity_ids: list[str]
    ) -> list[dict[str, object]]: ...
    def build_case_bundle(
        self, *, trigger_artifact_id: str, new_evidence_ids: list[str]
    ) -> CaseBundle: ...
    async def record_no_material_delta(
        self,
        *,
        trigger_artifact_id: str,
        reason: str,
        delta: DecisionDeltaProposal | None,
        context: WorkflowContext,
    ) -> None: ...
    async def record_delta_proposed(
        self, *, delta: DecisionDeltaProposal, context: WorkflowContext
    ) -> None: ...
    async def record_delta_rejected(
        self, *, delta: DecisionDeltaProposal, reasons: tuple[str, ...], context: WorkflowContext
    ) -> None: ...
    async def stage_delta(
        self,
        *,
        case_id: str,
        delta: DecisionDeltaProposal,
        review: ReviewDecision,
        context: WorkflowContext,
    ) -> None: ...
    async def record_case_human_review(
        self,
        *,
        case_id: str,
        delta: DecisionDeltaProposal,
        review: ReviewDecision,
        context: WorkflowContext,
    ) -> None: ...
    async def record_unavailable_artifact(
        self, event: SourceEvent, artifact: Artifact, *, context: WorkflowContext
    ) -> None: ...
    async def record_artifact_stored(
        self, artifact: Artifact, *, context: WorkflowContext
    ) -> None: ...
    async def record_rejected_extraction(
        self, artifact: Artifact, reasons: tuple[str, ...], *, context: WorkflowContext
    ) -> None: ...
    async def stage_inquiry(
        self, *, case_id: str, inquiry: InquiryProposal, context: WorkflowContext
    ) -> None: ...
    async def record_inquiry_rejected(
        self,
        *,
        case_id: str,
        inquiry: InquiryProposal,
        reasons: tuple[str, ...],
        context: WorkflowContext,
    ) -> None: ...


class ExtractionVerdict(Protocol):
    @property
    def ok(self) -> bool: ...
    @property
    def reasons(self) -> tuple[str, ...]: ...


class PolicyService(Protocol):
    def assert_source_event_allowed(self, event: SourceEvent) -> None: ...
    def validate_artifact(self, artifact: Artifact) -> None: ...
    def validate_document_extraction(
        self, extraction: DocumentExtraction, artifact: Artifact
    ) -> ExtractionVerdict: ...
    def validate_media_extraction(
        self, extraction: MediaExtraction, artifact: Artifact
    ) -> ExtractionVerdict: ...
    def validate_entity_links(
        self, links: EntityLinkBatch, extraction: DocumentExtraction
    ) -> None: ...
    def validate_case_link(self, proposal: CaseLinkProposal) -> None: ...
    def validate_delta(
        self, delta: DecisionDeltaProposal, case_bundle: CaseBundle
    ) -> ExtractionVerdict: ...
    def review_is_stageable(self, review: ReviewDecision, delta: DecisionDeltaProposal) -> bool: ...
    def validate_inquiry(
        self, inquiry: InquiryProposal, case_bundle: CaseBundle
    ) -> ExtractionVerdict: ...


class AgentService(Protocol):
    async def document_evidence(
        self, artifact: Artifact, *, context: WorkflowContext
    ) -> DocumentExtraction: ...
    async def media_evidence(
        self, artifact: Artifact, *, context: WorkflowContext
    ) -> MediaExtraction: ...
    async def entity_resolution(
        self, extraction: DocumentExtraction, *, context: WorkflowContext
    ) -> EntityLinkBatch: ...
    async def case_linker(
        self,
        extraction: DocumentExtraction,
        entity_links: EntityLinkBatch,
        case_summaries: list[dict[str, object]],
        *,
        context: WorkflowContext,
    ) -> list[CaseLinkProposal]: ...
    async def delta_investigator(
        self, case_bundle: CaseBundle, *, context: WorkflowContext
    ) -> DecisionDeltaProposal: ...
    async def quality_reviewer(
        self,
        delta: DecisionDeltaProposal,
        case_bundle: CaseBundle,
        *,
        context: WorkflowContext,
    ) -> ReviewDecision: ...
    async def inquiry_planner(
        self,
        delta: DecisionDeltaProposal,
        case_bundle: CaseBundle,
        *,
        context: WorkflowContext,
    ) -> InquiryProposal: ...


class RouteRegistry(Protocol):
    def requires_document_extraction(self, artifact: Artifact) -> bool: ...
    def requires_media_extraction(self, artifact: Artifact) -> bool: ...
    def is_unavailable(self, artifact: Artifact) -> bool: ...


class IdempotencyService(Protocol):
    def source_job_key(self, event: SourceEvent, *, workflow_version: str) -> str: ...


class CityDocumentWorkflow:
    """MVP workflow for one approved City document/structured-source replay route.

    Important: agents return proposals. Only PolicyService + CaseRepository write durable state.
    """

    WORKFLOW_VERSION = "city-document.v1"

    def __init__(
        self,
        *,
        artifacts: ArtifactVault,
        jobs: JobRepository,
        cases: CaseRepository,
        policy: PolicyService,
        agents: AgentService,
        routes: RouteRegistry,
        idempotency: IdempotencyService,
    ) -> None:
        self._artifacts = artifacts
        self._jobs = jobs
        self._cases = cases
        self._policy = policy
        self._agents = agents
        self._routes = routes
        self._idempotency = idempotency

    async def run(self, event: SourceEvent, *, trace_id: str) -> WorkflowResult:
        self._policy.assert_source_event_allowed(event)
        job_key = self._idempotency.source_job_key(event, workflow_version=self.WORKFLOW_VERSION)
        context = WorkflowContext(trace_id=trace_id, job_key=job_key)

        if await self._jobs.exists_terminal(job_key):
            return WorkflowResult(
                status=JobStatus.DUPLICATE_SUPPRESSED,
                job_key=job_key,
                reason="An identical terminal source-version workflow already exists.",
            )

        await self._jobs.start(job_key, context=context)
        try:
            artifact = await self._artifacts.fetch_and_store(event, context=context)
            self._policy.validate_artifact(artifact)

            if self._routes.is_unavailable(artifact):
                await self._cases.record_unavailable_artifact(event, artifact, context=context)
                await self._jobs.succeed(job_key, context=context)
                return WorkflowResult(
                    status=JobStatus.NOT_PUBLISHED,
                    job_key=job_key,
                    reason=artifact.availability_reason,
                )

            await self._cases.record_artifact_stored(artifact, context=context)

            if self._routes.requires_document_extraction(artifact):
                extraction = await self._agents.document_evidence(artifact, context=context)
                verdict = self._policy.validate_document_extraction(extraction, artifact)
            elif self._routes.requires_media_extraction(artifact):
                # Meeting evidence: the agent reads bounded transcript spans, the media gate
                # validates timestamps/quotes/labels, then the converted extraction joins the
                # exact same tail (ledger append, case link, delta) as a document.
                media = await self._agents.media_evidence(artifact, context=context)
                verdict = self._policy.validate_media_extraction(media, artifact)
                extraction = media.to_document_extraction()
            else:
                await self._jobs.succeed(job_key, context=context)
                return WorkflowResult(
                    status=JobStatus.NO_ACTION,
                    job_key=job_key,
                    reason="The City MVP document route does not handle this artifact type.",
                )
            if not verdict.ok:
                await self._cases.record_rejected_extraction(
                    artifact, verdict.reasons, context=context
                )
                await self._jobs.succeed(job_key, context=context)
                return WorkflowResult(
                    status=JobStatus.EXTRACTION_REJECTED,
                    job_key=job_key,
                    reason="; ".join(verdict.reasons),
                )
            await self._cases.append_validated_extraction(extraction, context=context)

            entity_links = await self._agents.entity_resolution(extraction, context=context)
            self._policy.validate_entity_links(entity_links, extraction)
            candidate_entities = entity_links.confirmed_or_candidate_entity_ids()
            case_summaries = await self._cases.active_case_summaries(
                candidate_entity_ids=candidate_entities
            )
            proposals = await self._agents.case_linker(
                extraction,
                entity_links,
                case_summaries,
                context=context,
            )

            staged_case_ids: list[str] = []
            for proposal in proposals:
                self._policy.validate_case_link(proposal)
                case_id = proposal.case_id
                if case_id is None or not proposal.is_actionable_existing_case_link():
                    continue
                if await self._compare_and_stage(artifact, proposal, context=context):
                    staged_case_ids.append(case_id)

            await self._jobs.succeed(job_key, context=context)
            return WorkflowResult(
                status=JobStatus.SUCCEEDED,
                job_key=job_key,
                staged_case_ids=tuple(staged_case_ids),
            )
        except Exception as exc:
            # Production implementation maps known transient failures to retry/dead-letter state.
            # The outline keeps raw source/model content out of exception messages.
            await self._jobs.fail(job_key, error_code=type(exc).__name__, context=context)
            raise

    async def _compare_and_stage(
        self, artifact: Artifact, proposal: CaseLinkProposal, *, context: WorkflowContext
    ) -> bool:
        """Promise pile vs later pile → proposed delta → checks → review. True if staged."""
        bundle = self._cases.build_case_bundle(
            trigger_artifact_id=artifact.artifact_id,
            new_evidence_ids=proposal.linked_evidence_ids,
        )
        if not bundle.later_evidence:
            await self._cases.record_no_material_delta(
                trigger_artifact_id=artifact.artifact_id,
                reason="no later evidence to compare against the promise",
                delta=None,
                context=context,
            )
            return False

        delta = await self._agents.delta_investigator(bundle, context=context)
        verdict = self._policy.validate_delta(delta, bundle)
        if not verdict.ok:
            await self._cases.record_delta_rejected(
                delta=delta, reasons=verdict.reasons, context=context
            )
            return False
        if delta.result_type is not DeltaResultType.DECISION_DELTA:
            await self._cases.record_no_material_delta(
                trigger_artifact_id=artifact.artifact_id,
                reason=f"agent result {delta.result_type}",
                delta=delta,
                context=context,
            )
            return False

        await self._cases.record_delta_proposed(delta=delta, context=context)
        review = await self._agents.quality_reviewer(delta, bundle, context=context)
        if self._policy.review_is_stageable(review, delta):
            await self._cases.stage_delta(
                case_id=delta.case_id, delta=delta, review=review, context=context
            )
            await self._plan_inquiry(delta, bundle, context=context)
            return True
        await self._cases.record_case_human_review(
            case_id=delta.case_id, delta=delta, review=review, context=context
        )
        return False

    async def _plan_inquiry(
        self, delta: DecisionDeltaProposal, bundle: CaseBundle, *, context: WorkflowContext
    ) -> None:
        """Staged delta → planner proposal → deterministic gate → INQUIRY_STAGED or refusal."""
        inquiry = await self._agents.inquiry_planner(delta, bundle, context=context)
        verdict = self._policy.validate_inquiry(inquiry, bundle)
        if verdict.ok:
            await self._cases.stage_inquiry(
                case_id=delta.case_id, inquiry=inquiry, context=context
            )
            return
        await self._cases.record_inquiry_rejected(
            case_id=delta.case_id, inquiry=inquiry, reasons=verdict.reasons, context=context
        )
