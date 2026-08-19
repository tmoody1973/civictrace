"""AgentService for Slice 1: Document Evidence via an injected runner; the rest is deterministic.

Entity Resolution and Case Linker are empty no-ops here (Slice 2). Delta/Quality raise.
"""

from __future__ import annotations

from app.agents.factory import AgentDefinition, StructuredAgentRunner
from app.orchestration.workflow import WorkflowContext
from app.schemas.case import CaseLinkProposal, DecisionDeltaProposal, ReviewDecision
from app.schemas.evidence import DocumentExtraction, EntityLinkBatch
from app.schemas.source import Artifact

DOCUMENT_EVIDENCE_DEFINITION = AgentDefinition(
    name="civictrace-document_evidence",
    role="document_evidence",
    model="fixture",  # ponytail: real model id comes from CivicTraceAgentFactory in Slice 2
    output_model=DocumentExtraction,
    tools=(),
)


class DocumentEvidenceAgentService:
    def __init__(self, runner: StructuredAgentRunner) -> None:
        self._runner = runner

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
        return []

    async def delta_investigator(
        self, case_bundle: dict[str, object], *, context: WorkflowContext
    ) -> DecisionDeltaProposal:
        raise NotImplementedError("Delta Investigator arrives in Slice 2")

    async def quality_reviewer(
        self,
        delta: DecisionDeltaProposal,
        case_bundle: dict[str, object],
        *,
        context: WorkflowContext,
    ) -> ReviewDecision:
        raise NotImplementedError("Quality Reviewer arrives in Slice 2")
