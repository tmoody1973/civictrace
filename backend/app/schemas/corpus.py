"""Reviewed replay-corpus manifest (docs/sources/corpus-manifest.yaml). Pure: pydantic + stdlib."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ArtifactAvailability
from app.schemas.source import SourceEvent


class RequiredAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int


class ExpectedBasis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prior_files: list[str]
    prior_intro_dates: list[date]


class MediaSegment(BaseModel):
    """A bounded time range inside a meeting recording (Slice 6, MOO-715).

    Segment bounds come from Legistar's own EventItemVideoIndex values — the official
    per-agenda-item timestamps — never from guessing.
    """

    model_config = ConfigDict(extra="forbid")

    start_seconds: int
    end_seconds: int
    basis: str


class ManifestArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    role: str
    source_id: str
    external_id: str
    canonical_url: str | None
    title: str | None
    retrieved_at: datetime
    content_hash: str | None
    media_type: str | None
    local_path: str | None
    availability: ArtifactAvailability
    availability_reason: str | None = None
    legistar_file: str | None = None
    legistar_matter_id: int | None = None
    legistar_attachment_id: int | None = None
    matter_url: str | None = None
    council_action_date: date | None = None
    byte_length: int | None = None
    page_count: int | None = None
    required_anchors: list[RequiredAnchor] = Field(default_factory=list)
    expected_basis: ExpectedBasis | None = None
    proof_of_absence: str | None = None
    # Media-only fields (Slice 6, MOO-715): meeting recordings referenced from Legistar.
    legistar_event_id: int | None = None
    granicus_clip_id: int | None = None
    duration_seconds: int | None = None
    focus_segment: MediaSegment | None = None
    # Committed diarized transcript of the focus segment (MOO-716), relative to fixture_dir.
    transcript_path: str | None = None


class DuplicateEventFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str


class CorpusManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    corpus_id: str
    jurisdiction: str
    case_id: str
    case_topic: str
    fixture_dir: str
    artifacts: list[ManifestArtifact]
    # Meeting recordings (Slice 6). A separate list on purpose: the document replay
    # iterates `artifacts`; media flows through the transcription pipeline instead.
    media_artifacts: list[ManifestArtifact] = Field(default_factory=list)
    duplicate_event_fixture: DuplicateEventFixture
    required_demo_outcomes: list[str] = Field(default_factory=list)
    prohibited_fixture_content: list[str] = Field(default_factory=list)

    def entry(self, artifact_id: str) -> ManifestArtifact:
        """Look up any reviewed artifact, document or media, by id."""
        by_id = {
            entry.artifact_id: entry for entry in (*self.artifacts, *self.media_artifacts)
        }
        return by_id[artifact_id]

    def media_entry(self, artifact_id: str) -> ManifestArtifact:
        by_id = {entry.artifact_id: entry for entry in self.media_artifacts}
        return by_id[artifact_id]

    def is_media(self, artifact_id: str) -> bool:
        return any(entry.artifact_id == artifact_id for entry in self.media_artifacts)

    def source_event(self, artifact_id: str) -> SourceEvent:
        entry = self.entry(artifact_id)
        return SourceEvent(
            source_event_id=f"{self.corpus_id}/{entry.artifact_id}",
            source_id=entry.source_id,
            jurisdiction=self.jurisdiction,
            artifact_id=entry.artifact_id,
            external_id=entry.external_id,
            canonical_url=entry.canonical_url,
            title=entry.title,
            media_type=entry.media_type,
            content_hash=entry.content_hash,
            observed_at=entry.retrieved_at,
        )
