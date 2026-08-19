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
from app.schemas.case import LedgerEvent
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
    def __init__(self, *, case_id: str, clock: Callable[[], datetime]) -> None:
        self._case_id = case_id
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

    async def active_case_summaries(
        self, *, candidate_entity_ids: list[str]
    ) -> list[dict[str, object]]:
        return []

    async def frozen_case_bundle(
        self, case_id: str, *, later_evidence_ids: list[str]
    ) -> dict[str, object]:
        raise NotImplementedError("Decision Delta bundles arrive in Slice 2")

    async def stage_delta(
        self, *, case_id: str, delta: object, review: object, context: WorkflowContext
    ) -> None:
        raise NotImplementedError("Decision Delta staging arrives in Slice 2")

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
