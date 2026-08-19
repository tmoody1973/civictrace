"""Append-only Promise Ledger. In-memory implementation for Slice 1.

There is deliberately no update/delete. A ledger event's id is derived from
(job_key, event_type, payload_ref), so re-appending the same fact is a no-op.

# ponytail: single-case ledger; case linking + Firestore implementation in Slice 2.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum

from app.domain.enums import LedgerEventType
from app.orchestration.workflow import WorkflowContext
from app.schemas.case import (
    BundleEvidence,
    CaseBundle,
    DecisionDeltaProposal,
    LedgerEvent,
    ReviewDecision,
)
from app.schemas.evidence import DocumentExtraction
from app.schemas.source import Artifact, SourceEvent

SYSTEM_ACTOR = "system"


class AppendOutcome(StrEnum):
    APPENDED = "APPENDED"
    DUPLICATE_SUPPRESSED = "DUPLICATE_SUPPRESSED"


def ledger_event_id(job_key: str, event_type: LedgerEventType, payload_ref: str) -> str:
    material = "\n".join((job_key, event_type, payload_ref)).encode("utf-8")
    return "evt_" + hashlib.sha256(material).hexdigest()[:32]


class InMemoryLedger:
    def __init__(
        self,
        *,
        case_id: str,
        clock: Callable[[], datetime],
        original_artifact_ids: frozenset[str],
        case_topic: str = "",
    ) -> None:
        """original_artifact_ids is required: without it every record looks 'later' and a delta
        could compare the promise with itself."""
        self._case_id = case_id
        self._case_topic = case_topic
        self._original_artifact_ids = original_artifact_ids
        self._clock = clock
        self._events: list[LedgerEvent] = []
        self._seen: set[str] = set()

    def append(self, event: LedgerEvent) -> AppendOutcome:
        if event.event_id in self._seen:
            return AppendOutcome.DUPLICATE_SUPPRESSED
        self._seen.add(event.event_id)
        self._events.append(event)
        return AppendOutcome.APPENDED

    def events(self) -> list[LedgerEvent]:
        return list(self._events)

    # --- CaseRepository protocol (workflow.py) ---------------------------------

    async def append_validated_extraction(
        self, extraction: DocumentExtraction, *, context: WorkflowContext
    ) -> None:
        for item in extraction.evidence:
            self.append(
                self._new_event(
                    context, LedgerEventType.EVIDENCE_ACCEPTED, item.evidence_id, evidence=item
                )
            )

    async def record_artifact_stored(self, artifact: Artifact, *, context: WorkflowContext) -> None:
        self.append(
            self._new_event(
                context, LedgerEventType.ARTIFACT_STORED, artifact.artifact_id, artifact=artifact
            )
        )

    async def record_unavailable_artifact(
        self, event: SourceEvent, artifact: Artifact, *, context: WorkflowContext
    ) -> None:
        self.append(
            self._new_event(
                context,
                LedgerEventType.ARTIFACT_NOT_PUBLISHED,
                artifact.artifact_id,
                artifact=artifact,
                reason=artifact.availability_reason,
            )
        )

    async def record_rejected_extraction(
        self, artifact: Artifact, reasons: tuple[str, ...], *, context: WorkflowContext
    ) -> None:
        self.append(
            self._new_event(
                context,
                LedgerEventType.EXTRACTION_REJECTED,
                artifact.artifact_id,
                artifact=artifact,
                reason="; ".join(reasons),
            )
        )

    async def active_case_summaries(
        self, *, candidate_entity_ids: list[str]
    ) -> list[dict[str, object]]:
        return []

    async def frozen_case_bundle(
        self, case_id: str, *, later_evidence_ids: list[str]
    ) -> dict[str, object]:
        """Returned as a dict to satisfy the outline protocol; callers use build_case_bundle()."""
        return self.build_case_bundle(
            trigger_artifact_id="", new_evidence_ids=later_evidence_ids
        ).model_dump()

    def build_case_bundle(
        self, *, trigger_artifact_id: str, new_evidence_ids: list[str]
    ) -> CaseBundle:
        """Freeze the promise pile and the later pile from everything accepted so far."""
        urls = {
            e.artifact.artifact_id: e.artifact.canonical_url for e in self._events if e.artifact
        }
        original: list[BundleEvidence] = []
        later: list[BundleEvidence] = []
        for event in self._events:
            if event.event_type is not LedgerEventType.EVIDENCE_ACCEPTED or event.evidence is None:
                continue
            is_original = event.evidence.artifact_id in self._original_artifact_ids
            item = BundleEvidence(
                evidence=event.evidence,
                canonical_url=urls.get(event.evidence.artifact_id),
                artifact_role="original_commitment" if is_original else "later_evidence",
            )
            (original if is_original else later).append(item)
        not_published = [
            e.artifact.artifact_id
            for e in self._events
            if e.event_type is LedgerEventType.ARTIFACT_NOT_PUBLISHED and e.artifact
        ]
        return CaseBundle(
            case_id=self._case_id,
            case_topic=self._case_topic,
            trigger_artifact_id=trigger_artifact_id,
            original_evidence=original,
            later_evidence=later,
            new_evidence_ids=list(new_evidence_ids),
            not_published_artifact_ids=not_published,
        )

    async def record_no_material_delta(
        self,
        *,
        trigger_artifact_id: str,
        reason: str,
        delta: DecisionDeltaProposal | None,
        context: WorkflowContext,
    ) -> None:
        self.append(
            self._new_event(
                context,
                LedgerEventType.NO_MATERIAL_DELTA,
                trigger_artifact_id,
                delta=delta,
                reason=reason,
            )
        )

    async def record_delta_proposed(
        self, *, delta: DecisionDeltaProposal, context: WorkflowContext
    ) -> None:
        self.append(
            self._new_event(context, LedgerEventType.DELTA_PROPOSED, delta.case_id, delta=delta)
        )

    async def record_delta_rejected(
        self, *, delta: DecisionDeltaProposal, reasons: tuple[str, ...], context: WorkflowContext
    ) -> None:
        self.append(
            self._new_event(
                context,
                LedgerEventType.DELTA_REJECTED,
                delta.case_id,
                delta=delta,
                reason="; ".join(reasons),
            )
        )

    async def stage_delta(
        self,
        *,
        case_id: str,
        delta: DecisionDeltaProposal,
        review: ReviewDecision,
        context: WorkflowContext,
    ) -> None:
        self.append(
            self._new_event(
                context, LedgerEventType.DELTA_STAGED, case_id, delta=delta, review=review
            )
        )

    async def record_case_human_review(
        self,
        *,
        case_id: str,
        delta: DecisionDeltaProposal,
        review: ReviewDecision,
        context: WorkflowContext,
    ) -> None:
        reason = "; ".join(review.blocking_reasons()) or f"reviewer outcome {review.outcome}"
        self.append(
            self._new_event(
                context,
                LedgerEventType.CASE_HUMAN_REVIEW,
                case_id,
                delta=delta,
                review=review,
                reason=reason,
            )
        )

    def _new_event(
        self,
        context: WorkflowContext,
        event_type: LedgerEventType,
        payload_ref: str,
        **details: object,
    ) -> LedgerEvent:
        return LedgerEvent(
            event_id=ledger_event_id(context.job_key, event_type, payload_ref),
            case_id=self._case_id,
            job_key=context.job_key,
            event_type=event_type,
            payload_ref=payload_ref,
            occurred_at=self._clock(),
            actor=context.actor or SYSTEM_ACTOR,
            **details,  # type: ignore[arg-type]
        )
