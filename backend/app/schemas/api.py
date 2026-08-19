"""Public API envelopes and the Evidence Trace view. Pure: pydantic + stdlib.

The trace is built only from validated ledger fields — never from model prose.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import AnchorType, LedgerEventType


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


class TraceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    events: list[TraceEventView]


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
