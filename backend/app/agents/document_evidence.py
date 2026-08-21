"""AgentService for Slice 2: Document Evidence, Delta Investigator, and Quality Reviewer via an
injected runner. Entity Resolution is an empty no-op (later slice). Case link is deterministic:
one case per corpus (# ponytail: agentic Case Linker when there is more than one case).
"""

from __future__ import annotations

from collections.abc import Callable

from app.agents.factory import AgentDefinition, StructuredAgentRunner
from app.domain.enums import LinkStatus
from app.orchestration.workflow import WorkflowContext
from app.schemas.case import (
    CaseBundle,
    CaseLinkProposal,
    DecisionDeltaProposal,
    ReviewDecision,
    ReviewRequest,
)
from app.schemas.evidence import (
    DocumentEvidenceTask,
    DocumentExtraction,
    EntityCandidate,
    EntityEvidenceSummary,
    EntityLinkBatch,
    EntityResolutionTask,
    MediaEvidenceTask,
    MediaExtraction,
)
from app.schemas.inquiry import InquiryProposal, InquiryTask
from app.schemas.source import Artifact

DOCUMENT_EVIDENCE_DEFINITION = AgentDefinition(
    name="civictrace-document_evidence",
    role="document_evidence",
    model="fixture",  # ponytail: real model id comes from CivicTraceAgentFactory in Slice 2.2
    output_model=DocumentExtraction,
    tools=(),
)
DELTA_INVESTIGATOR_DEFINITION = AgentDefinition(
    name="civictrace-delta_investigator",
    role="delta_investigator",
    model="fixture",
    output_model=DecisionDeltaProposal,
    tools=(),
)
QUALITY_REVIEWER_DEFINITION = AgentDefinition(
    name="civictrace-quality_reviewer",
    role="quality_reviewer",
    model="fixture",
    output_model=ReviewDecision,
    tools=(),
)
INQUIRY_PLANNER_DEFINITION = AgentDefinition(
    name="civictrace-inquiry_planner",
    role="inquiry_planner",
    model="fixture",
    output_model=InquiryProposal,
    tools=(),
)
MEDIA_EVIDENCE_DEFINITION = AgentDefinition(
    name="civictrace-media_evidence",
    role="media_evidence",
    model="fixture",
    output_model=MediaExtraction,
    tools=(),
)
ENTITY_RESOLUTION_DEFINITION = AgentDefinition(
    name="civictrace-entity_resolution",
    role="entity_resolution",
    model="fixture",
    output_model=EntityLinkBatch,
    tools=(),
)


class DocumentEvidenceAgentService:
    def __init__(
        self,
        runner: StructuredAgentRunner,
        *,
        case_id: str,
        hint_pages: dict[str, list[int]] | None = None,
        media_task_for: Callable[[str], MediaEvidenceTask] | None = None,
        entity_candidates: list[EntityCandidate] | None = None,
    ) -> None:
        self._runner = runner
        self._case_id = case_id
        self._hint_pages = hint_pages or {}
        self._media_task_for = media_task_for
        self._entity_candidates = entity_candidates or []

    async def document_evidence(
        self,
        artifact: Artifact,
        *,
        context: WorkflowContext,
        revision_notes: list[str] | None = None,
    ) -> DocumentExtraction:
        task = DocumentEvidenceTask(
            artifact_id=artifact.artifact_id,
            title=artifact.title,
            canonical_url=artifact.canonical_url,
            media_type=artifact.media_type,
            page_count=artifact.page_count,
            hint_pages=self._hint_pages.get(artifact.artifact_id, []),
            revision_notes=revision_notes or [],
        )
        result = await self._runner.run(
            DOCUMENT_EVIDENCE_DEFINITION, task, trace_id=context.trace_id
        )
        return DocumentExtraction.model_validate(result.model_dump())

    async def media_evidence(
        self, artifact: Artifact, *, context: WorkflowContext
    ) -> MediaExtraction:
        if self._media_task_for is None:
            raise ValueError(f"{artifact.artifact_id}: no media task builder configured")
        task = self._media_task_for(artifact.artifact_id)
        result = await self._runner.run(
            MEDIA_EVIDENCE_DEFINITION, task, trace_id=context.trace_id
        )
        return MediaExtraction.model_validate(result.model_dump())

    async def entity_resolution(
        self, extraction: DocumentExtraction, *, context: WorkflowContext
    ) -> EntityLinkBatch:
        # No candidates means nothing to match against (fake/CI mode, or an empty
        # registry) — an empty batch, never an unconstrained agent call.
        if not self._entity_candidates or not extraction.evidence:
            return EntityLinkBatch(links=[])
        task = EntityResolutionTask(
            artifact_id=extraction.artifact_id,
            evidence=[
                EntityEvidenceSummary(
                    evidence_id=item.evidence_id,
                    neutral_statement=item.neutral_statement,
                    verbatim_excerpt=item.verbatim_excerpt,
                )
                for item in extraction.evidence
            ],
            candidates=self._entity_candidates,
        )
        result = await self._runner.run(
            ENTITY_RESOLUTION_DEFINITION, task, trace_id=context.trace_id
        )
        return EntityLinkBatch.model_validate(result.model_dump())

    async def case_linker(
        self,
        extraction: DocumentExtraction,
        entity_links: EntityLinkBatch,
        case_summaries: list[dict[str, object]],
        *,
        context: WorkflowContext,
    ) -> list[CaseLinkProposal]:
        return [
            CaseLinkProposal(
                case_id=self._case_id,
                linked_evidence_ids=[item.evidence_id for item in extraction.evidence],
                link_status=LinkStatus.CONFIRMED,
                rationale="corpus manifest binds every artifact to this case",
            )
        ]

    async def delta_investigator(
        self, case_bundle: CaseBundle, *, context: WorkflowContext
    ) -> DecisionDeltaProposal:
        result = await self._runner.run(
            DELTA_INVESTIGATOR_DEFINITION, case_bundle, trace_id=context.trace_id
        )
        return DecisionDeltaProposal.model_validate(result.model_dump())

    async def quality_reviewer(
        self,
        delta: DecisionDeltaProposal,
        case_bundle: CaseBundle,
        *,
        context: WorkflowContext,
    ) -> ReviewDecision:
        request = ReviewRequest(
            trigger_artifact_id=case_bundle.trigger_artifact_id, delta=delta, bundle=case_bundle
        )
        result = await self._runner.run(
            QUALITY_REVIEWER_DEFINITION, request, trace_id=context.trace_id
        )
        return ReviewDecision.model_validate(result.model_dump())

    async def inquiry_planner(
        self,
        delta: DecisionDeltaProposal,
        case_bundle: CaseBundle,
        *,
        context: WorkflowContext,
    ) -> InquiryProposal:
        task = InquiryTask(
            case_id=delta.case_id,
            case_topic=case_bundle.case_topic,
            category=delta.category,
            neutral_summary=delta.neutral_summary,
            what_is_established=list(delta.what_is_established),
            what_is_not_established=list(delta.what_is_not_established),
            next_evidence_needed=delta.next_evidence_needed,
            original_evidence_ids=list(delta.original_evidence_ids),
            later_evidence_ids=list(delta.later_evidence_ids),
            not_published_artifact_ids=list(case_bundle.not_published_artifact_ids),
        )
        result = await self._runner.run(
            INQUIRY_PLANNER_DEFINITION, task, trace_id=context.trace_id
        )
        return InquiryProposal.model_validate(result.model_dump())
