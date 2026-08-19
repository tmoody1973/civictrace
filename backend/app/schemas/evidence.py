"""Anchored evidence contracts. Pure: pydantic + stdlib.

The shape of Evidence/DocumentExtraction is the contract with
backend/tests/fixtures/milwaukee-city-promise-ledger-demo-v1/fixture_extraction.json.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import AnchorType, EvidenceObjectType, EvidenceStatus, LinkStatus


class EvidenceAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    anchor_type: AnchorType
    anchor_value: str


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    artifact_id: str
    object_type: EvidenceObjectType
    verbatim_excerpt: str
    neutral_statement: str
    anchors: list[EvidenceAnchor]
    status: EvidenceStatus
    limitations: list[str] = Field(default_factory=list)


class DocumentEvidenceTask(BaseModel):
    """Bounded task for the Document Evidence Agent: metadata + page hints, never page text.

    The agent must call its read-only page tool to see any words. `hint_pages` are the
    manifest's required_anchors pages — where a human said the load-bearing facts live —
    offered as a starting point, not as the answer.
    """

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    title: str | None = None
    canonical_url: str | None = None
    media_type: str | None = None
    page_count: int | None = None
    hint_pages: list[int] = Field(default_factory=list)


class DocumentExtraction(BaseModel):
    """Typed proposal from the Document Evidence Agent (or its fixture stand-in)."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    agent_name: str
    agent_version: str
    evidence: list[Evidence]


class EntityLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    entity_id: str
    link_status: LinkStatus
    rationale: str


class EntityLinkBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    links: list[EntityLink]

    def confirmed_or_candidate_entity_ids(self) -> list[str]:
        return [
            link.entity_id for link in self.links if link.link_status is not LinkStatus.REJECTED
        ]
