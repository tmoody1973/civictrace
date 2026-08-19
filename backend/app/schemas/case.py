"""Case, case-link, Decision Delta, and review contracts. Pure: pydantic + stdlib."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DeltaCategory, LinkStatus, ReviewOutcome


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    jurisdiction: str
    case_topic: str
    original_evidence_ids: list[str] = Field(default_factory=list)


class CaseLinkProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str | None
    linked_evidence_ids: list[str]
    link_status: LinkStatus
    rationale: str

    def is_actionable_existing_case_link(self) -> bool:
        return self.case_id is not None and self.link_status is LinkStatus.CONFIRMED


class DecisionDelta(BaseModel):
    """A comparison of a Promise and later public record. Never a verdict."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    category: DeltaCategory
    neutral_summary: str
    original_evidence_ids: list[str]
    later_evidence_ids: list[str]
    what_is_established: list[str]
    what_is_not_established: list[str]
    next_evidence_needed: str | None
    requires_human_review: bool = True


class DecisionDeltaProposal(DecisionDelta):
    """DecisionDelta as proposed by an agent; becomes durable only after validation."""

    proposed_by_agent: str
    agent_version: str


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: ReviewOutcome
    blocking_issues: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def is_stageable(self) -> bool:
        return self.outcome is ReviewOutcome.APPROVE and not self.blocking_issues
