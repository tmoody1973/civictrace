"""AgentService for Slice 2: Document Evidence and Delta Investigator via an injected runner.

Entity Resolution is an empty no-op (later slice). Case link is deterministic: one case per
corpus (# ponytail: agentic Case Linker when there is more than one case). Quality Reviewer is a
placeholder until Slice 2.4 — it never approves, so every proposed delta lands in human review.
"""

from __future__ import annotations

from app.agents.factory import AgentDefinition, StructuredAgentRunner
from app.domain.enums import LinkStatus, ReviewOutcome
from app.orchestration.workflow import WorkflowContext
from app.schemas.case import CaseBundle, CaseLinkProposal, DecisionDeltaProposal, ReviewDecision
from app.schemas.evidence import DocumentExtraction, EntityLinkBatch
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
REVIEWER_UNAVAILABLE = "Quality Reviewer not yet available (Slice 2.4); human review required"


class DocumentEvidenceAgentService:
    def __init__(self, runner: StructuredAgentRunner, *, case_id: str) -> None:
        self._runner = runner
        self._case_id = case_id

    async def document_evidence(
        self, artifact: Artifact, *, context: WorkflowContext
    ) -> DocumentExtraction:
        result = await self._runner.run(
            DOCUMENT_EVIDENCE_DEFINITION, artifact, trace_id=context.trace_id
        )
        return DocumentExtraction.model_validate(result.model_dump())

    async def entity_resolution(
        self, extraction: DocumentExtraction, *, context: WorkflowContext
    ) -> EntityLinkBatch:
        return EntityLinkBatch(links=[])

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
        return ReviewDecision(outcome=ReviewOutcome.REVISE, blocking_issues=[REVIEWER_UNAVAILABLE])
