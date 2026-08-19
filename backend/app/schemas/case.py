"""Case, case-link, Decision Delta, and review contracts. Pure: pydantic + stdlib."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    DeltaCategory,
    DeltaResultType,
    LedgerEventType,
    LinkStatus,
    Materiality,
    ReviewOutcome,
)
from app.schemas.evidence import Evidence
from app.schemas.source import Artifact


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
    """DecisionDelta as proposed by an agent; becomes durable only after validation.

    Deliberate deviation from the design doc: no numeric `confidence`. CONTEXT.md keeps
    uncertainty as explicit states (UNKNOWN, NOT_PUBLISHED, HUMAN_REVIEW), not scores.
    """

    result_type: DeltaResultType
    materiality: Materiality
    limitations: list[str] = Field(default_factory=list)
    proposed_by_agent: str
    agent_version: str


class BundleEvidence(BaseModel):
    """One accepted evidence item plus where it came from, frozen for the Delta Investigator."""

    model_config = ConfigDict(extra="forbid")

    evidence: Evidence
    canonical_url: str | None
    artifact_role: str


class CaseBundle(BaseModel):
    """Frozen snapshot of one case's evidence: the promise pile and the later pile."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    case_topic: str
    trigger_artifact_id: str
    original_evidence: list[BundleEvidence]
    later_evidence: list[BundleEvidence]
    new_evidence_ids: list[str]
    not_published_artifact_ids: list[str] = Field(default_factory=list)

    def original_ids(self) -> set[str]:
        return {item.evidence.evidence_id for item in self.original_evidence}

    def later_ids(self) -> set[str]:
        return {item.evidence.evidence_id for item in self.later_evidence}


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: ReviewOutcome
    blocking_issues: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def is_stageable(self) -> bool:
        return self.outcome is ReviewOutcome.APPROVE and not self.blocking_issues


class LedgerEvent(BaseModel):
    """One append-only record in a Case's Promise Ledger. Never edited, never deleted."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    case_id: str
    job_key: str
    event_type: LedgerEventType
    payload_ref: str
    occurred_at: datetime
    actor: str
    evidence: Evidence | None = None
    artifact: Artifact | None = None
    delta: DecisionDeltaProposal | None = None
    review: ReviewDecision | None = None
    reason: str | None = None
