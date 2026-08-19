"""Inquiry Planner contracts (design doc §17). Pure: pydantic + stdlib.

The proposal is a draft next question, never a sent message. It becomes durable only
after validate_inquiry, and actionable only after a human ApprovalToken (MOO-702/704).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DeltaCategory, InquiryType


class InquiryTask(BaseModel):
    """The bounded evidence package the planner sees: the staged delta, nothing more."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    case_topic: str
    category: DeltaCategory
    neutral_summary: str
    what_is_established: list[str]
    what_is_not_established: list[str]
    next_evidence_needed: str | None
    original_evidence_ids: list[str]
    later_evidence_ids: list[str]
    not_published_artifact_ids: list[str] = Field(default_factory=list)


class InquiryProposal(BaseModel):
    """Design doc §17 output contract, verbatim fields. Never carries a destination."""

    model_config = ConfigDict(extra="forbid")

    inquiry_type: InquiryType
    proposed_question: str
    scope_rationale: str
    target_record_or_source: str
    supporting_evidence_ids: list[str]
    excluded_requests: list[str]
    approval_required: bool
    limitations: list[str] = Field(default_factory=list)
