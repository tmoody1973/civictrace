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


class MediaEvidenceTask(BaseModel):
    """Bounded task for the Media Evidence Agent: transcript metadata, never transcript text.

    The agent must call its read-only transcript-span tool to see any words.
    All times are milliseconds relative to the transcribed focus segment.
    """

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    transcript_id: str
    title: str | None = None
    canonical_url: str | None = None
    segment_start_seconds: int
    segment_end_seconds: int
    duration_ms: int
    speaker_labels: list[str] = Field(default_factory=list)
    focus_basis: str | None = None


class MediaEvidence(Evidence):
    """Evidence anchored to a transcript span; the speaker stays a diarization label.

    `speaker_label` may only be a label that appears in the anchored transcript span
    (the validator refuses a person's name here — naming is a separate gated step).
    """

    speaker_label: str | None = None


class MediaExtraction(BaseModel):
    """Typed proposal from the Media Evidence Agent (or its fixture stand-in)."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    transcript_id: str
    agent_name: str
    agent_version: str
    evidence: list[MediaEvidence]

    def to_document_extraction(self) -> DocumentExtraction:
        """Deterministic conversion for the ledger: fold the label into a limitation so the
        stored Evidence shape (and every downstream reader) stays unchanged."""
        items = []
        for item in self.evidence:
            limitations = list(item.limitations)
            if item.speaker_label:
                note = (
                    f"speaker {item.speaker_label} is a diarization label; "
                    "identity not established by this record"
                )
                if note not in limitations:
                    limitations.append(note)
            items.append(
                Evidence(
                    evidence_id=item.evidence_id,
                    artifact_id=item.artifact_id,
                    object_type=item.object_type,
                    verbatim_excerpt=item.verbatim_excerpt,
                    neutral_statement=item.neutral_statement,
                    anchors=list(item.anchors),
                    status=item.status,
                    limitations=limitations,
                )
            )
        return DocumentExtraction(
            artifact_id=self.artifact_id,
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            evidence=items,
        )


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
