"""Build the user-facing Evidence Trace from ledger events. Deterministic; no model text."""

from __future__ import annotations

from app.domain.enums import LedgerEventType
from app.schemas.api import (
    AnchorView,
    CaseCounts,
    CaseSummaryView,
    LatestDeltaView,
    TraceEventView,
    TraceResponse,
)
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
    return _case_view(event)


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
    rejected = event.event_type is LedgerEventType.EXTRACTION_REJECTED
    status = "REJECTED" if rejected else artifact.availability
    return TraceEventView(
        event_id=event.event_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        actor=event.actor,
        artifact_id=artifact.artifact_id,
        canonical_url=artifact.canonical_url,
        status=str(status),
        content_hash=artifact.content_hash,
        media_type=artifact.media_type,
        reason=event.reason,
    )


def _case_view(event: LedgerEvent) -> TraceEventView:
    """Delta / review / inquiry rows, from validated fields only."""
    delta, review, inquiry = event.delta, event.review, event.inquiry
    return TraceEventView(
        event_id=event.event_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        actor=event.actor,
        artifact_id=event.payload_ref,
        canonical_url=None,
        status=str(event.event_type),
        reason=event.reason,
        category=delta.category if delta else None,
        neutral_summary=delta.neutral_summary if delta else None,
        original_evidence_ids=list(delta.original_evidence_ids) if delta else [],
        later_evidence_ids=list(delta.later_evidence_ids) if delta else [],
        what_is_established=list(delta.what_is_established) if delta else [],
        what_is_not_established=list(delta.what_is_not_established) if delta else [],
        next_evidence_needed=delta.next_evidence_needed if delta else None,
        requires_human_review=delta.requires_human_review if delta else None,
        inquiry_type=inquiry.inquiry_type if inquiry else None,
        proposed_question=inquiry.proposed_question if inquiry else None,
        scope_rationale=inquiry.scope_rationale if inquiry else None,
        target_record_or_source=inquiry.target_record_or_source if inquiry else None,
        supporting_evidence_ids=list(inquiry.supporting_evidence_ids) if inquiry else [],
        excluded_requests=list(inquiry.excluded_requests) if inquiry else [],
        approval_token_id=event.approval.token_id if event.approval else None,
        approval_reviewer=event.approval.reviewer_name if event.approval else None,
        approval_expires_at=event.approval.expires_at if event.approval else None,
        review_outcome=review.outcome if review else None,
        blocking_issues=review.blocking_reasons() if review else [],
        review_notes=list(review.notes) if review else [],
    )


def build_case_summary(case_id: str, case_topic: str, events: list[LedgerEvent]) -> CaseSummaryView:
    """One-glance case state, counted from the ledger. No prose is generated here."""
    kinds = [event.event_type for event in events]
    counts = CaseCounts(
        artifacts_stored=kinds.count(LedgerEventType.ARTIFACT_STORED),
        evidence_accepted=kinds.count(LedgerEventType.EVIDENCE_ACCEPTED),
        not_published=kinds.count(LedgerEventType.ARTIFACT_NOT_PUBLISHED),
        extractions_rejected=kinds.count(LedgerEventType.EXTRACTION_REJECTED),
        deltas_proposed=kinds.count(LedgerEventType.DELTA_PROPOSED),
        deltas_rejected=kinds.count(LedgerEventType.DELTA_REJECTED),
    )
    staged = _last(events, LedgerEventType.DELTA_STAGED)
    human = _last(events, LedgerEventType.CASE_HUMAN_REVIEW)
    latest_event = staged or human
    state = "DELTA_STAGED" if staged else ("HUMAN_REVIEW" if human else "NO_DELTA")
    latest = _latest_delta_view(latest_event) if latest_event else None
    return CaseSummaryView(
        case_id=case_id,
        case_topic=case_topic,
        state=state,
        counts=counts,
        latest_delta=latest,
        next_evidence_needed=latest.next_evidence_needed if latest else None,
    )


def _last(events: list[LedgerEvent], kind: LedgerEventType) -> LedgerEvent | None:
    matching = [event for event in events if event.event_type is kind]
    return matching[-1] if matching else None


def _latest_delta_view(event: LedgerEvent) -> LatestDeltaView:
    assert event.delta is not None
    delta, review = event.delta, event.review
    return LatestDeltaView(
        category=delta.category,
        neutral_summary=delta.neutral_summary,
        original_evidence_ids=list(delta.original_evidence_ids),
        later_evidence_ids=list(delta.later_evidence_ids),
        what_is_established=list(delta.what_is_established),
        what_is_not_established=list(delta.what_is_not_established),
        next_evidence_needed=delta.next_evidence_needed,
        limitations=list(delta.limitations),
        requires_human_review=delta.requires_human_review,
        review_outcome=review.outcome if review else None,
        blocking_issues=review.blocking_reasons() if review else [],
    )
