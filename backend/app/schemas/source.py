"""Source events and immutable artifacts. Pure: pydantic + stdlib."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.domain.enums import ArtifactAvailability


class SourceEvent(BaseModel):
    """One observed public-source version, as reported by an approved adapter or replay."""

    model_config = ConfigDict(extra="forbid")

    source_event_id: str
    source_id: str
    jurisdiction: str
    artifact_id: str
    external_id: str
    canonical_url: str | None
    title: str | None = None
    media_type: str | None = None
    content_hash: str | None = None
    observed_at: datetime


class Artifact(BaseModel):
    """Immutable local copy plus provenance for one approved public-source version."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    source_id: str
    canonical_url: str | None
    external_id: str
    title: str | None
    media_type: str | None
    content_hash: str | None
    byte_length: int | None
    page_count: int | None
    storage_uri: str | None
    retrieved_at: datetime
    availability: ArtifactAvailability
    availability_reason: str | None = None

    @model_validator(mode="after")
    def _provenance_matches_availability(self) -> Artifact:
        if self.availability is ArtifactAvailability.AVAILABLE:
            missing = [
                name
                for name in ("content_hash", "storage_uri", "media_type")
                if getattr(self, name) is None
            ]
            if missing:
                raise ValueError(f"AVAILABLE artifact is missing provenance: {missing}")
        elif self.availability_reason is None:
            raise ValueError(f"{self.availability} artifact needs an availability_reason")
        return self
