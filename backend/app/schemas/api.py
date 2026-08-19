"""Public API envelopes and the Evidence Trace view. Pure: pydantic + stdlib.

The trace is built only from validated ledger fields — never from model prose.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AnchorType,
    DeltaCategory,
    InquiryType,
    LedgerEventType,
    ReviewOutcome,
)


class ApiEnvelope[T](BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    data: T | None
    error: str | None


class AnchorView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchor_type: AnchorType
    anchor_value: str


class TraceEventView(BaseModel):
    """One Evidence Trace row. Fields are None when they do not apply to the event type."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: LedgerEventType
    occurred_at: datetime
    actor: str
    artifact_id: str
    canonical_url: str | None
    status: str
    content_hash: str | None = None
    evidence_id: str | None = None
    anchors: list[AnchorView] = Field(default_factory=list)
    verbatim_excerpt: str | None = None
    neutral_statement: str | None = None
    limitations: list[str] = Field(default_factory=list)
    reason: str | None = None
    # delta rows: DELTA_PROPOSED / DELTA_REJECTED / DELTA_STAGED / CASE_HUMAN_REVIEW / NO_MATERIAL
    category: DeltaCategory | None = None
    neutral_summary: str | None = None
    original_evidence_ids: list[str] = Field(default_factory=list)
    later_evidence_ids: list[str] = Field(default_factory=list)
    what_is_established: list[str] = Field(default_factory=list)
    what_is_not_established: list[str] = Field(default_factory=list)
    next_evidence_needed: str | None = None
    requires_human_review: bool | None = None
    # inquiry rows: INQUIRY_STAGED / INQUIRY_REJECTED (MOO-703)
    inquiry_type: InquiryType | None = None
    proposed_question: str | None = None
    scope_rationale: str | None = None
    target_record_or_source: str | None = None
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    excluded_requests: list[str] = Field(default_factory=list)
    # approval rows (MOO-702)
    approval_token_id: str | None = None
    approval_reviewer: str | None = None
    approval_expires_at: datetime | None = None
    # review rows
    review_outcome: ReviewOutcome | None = None
    blocking_issues: list[str] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)


class TraceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    events: list[TraceEventView]


class CaseCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifacts_stored: int
    evidence_accepted: int
    not_published: int
    extractions_rejected: int
    deltas_proposed: int
    deltas_rejected: int


class LatestDeltaView(BaseModel):
    """The staged (or human-review) delta's validated fields — never free prose beyond them."""

    model_config = ConfigDict(extra="forbid")

    category: DeltaCategory
    neutral_summary: str
    original_evidence_ids: list[str]
    later_evidence_ids: list[str]
    what_is_established: list[str]
    what_is_not_established: list[str]
    next_evidence_needed: str | None
    limitations: list[str]
    requires_human_review: bool
    review_outcome: ReviewOutcome | None
    blocking_issues: list[str]


class CaseSummaryView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    case_topic: str
    state: str  # NO_DELTA | DELTA_STAGED | HUMAN_REVIEW
    counts: CaseCounts
    latest_delta: LatestDeltaView | None
    next_evidence_needed: str | None


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
