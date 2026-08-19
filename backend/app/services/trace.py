"""Build the user-facing Evidence Trace from ledger events. Deterministic; no model text."""

from __future__ import annotations

from app.domain.enums import LedgerEventType
from app.schemas.api import AnchorView, TraceEventView, TraceResponse
from app.schemas.case import LedgerEvent

ARTIFACT_EVENTS = frozenset(
    {
        LedgerEventType.ARTIFACT_STORED,
        LedgerEventType.ARTIFACT_NOT_PUBLISHED,
        LedgerEventType.EXTRACTION_REJECTED,
    }
)


def build_trace(case_id: str, events: list[LedgerEvent]) -> TraceResponse:
    urls = {
        event.artifact.artifact_id: event.artifact.canonical_url
        for event in events
        if event.artifact is not None
    }
    return TraceResponse(case_id=case_id, events=[_view(event, urls) for event in events])


def _view(event: LedgerEvent, urls: dict[str, str | None]) -> TraceEventView:
    if event.evidence is not None:
        return _evidence_view(event, urls.get(event.evidence.artifact_id))
    if event.artifact is not None and event.event_type in ARTIFACT_EVENTS:
        return _artifact_view(event)
    raise ValueError(f"ledger event {event.event_id} has neither evidence nor artifact")


def _evidence_view(event: LedgerEvent, canonical_url: str | None) -> TraceEventView:
    assert event.evidence is not None
    item = event.evidence
    return TraceEventView(
        event_id=event.event_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        actor=event.actor,
        artifact_id=item.artifact_id,
        canonical_url=canonical_url,
        status=item.status,
        evidence_id=item.evidence_id,
        anchors=[
            AnchorView(anchor_type=a.anchor_type, anchor_value=a.anchor_value) for a in item.anchors
        ],
        verbatim_excerpt=item.verbatim_excerpt,
        neutral_statement=item.neutral_statement,
        limitations=list(item.limitations),
    )


def _artifact_view(event: LedgerEvent) -> TraceEventView:
    assert event.artifact is not None
    artifact = event.artifact
    status = (
        "REJECTED"
        if event.event_type is LedgerEventType.EXTRACTION_REJECTED
        else artifact.availability
    )
    return TraceEventView(
        event_id=event.event_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        actor=event.actor,
        artifact_id=artifact.artifact_id,
        canonical_url=artifact.canonical_url,
        status=str(status),
        content_hash=artifact.content_hash,
        reason=event.reason,
    )
