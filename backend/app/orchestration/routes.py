"""Deterministic route selection by artifact availability and media type. No model involved."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.enums import ArtifactAvailability
from app.schemas.source import Artifact

DOCUMENT_MEDIA_TYPES = frozenset({"application/pdf", "text/html"})
MEETING_MEDIA_TYPES = frozenset({"video/mp4", "audio/flac"})


class RouteKind(StrEnum):
    DOCUMENT = "document"
    MEDIA = "media"
    UNAVAILABLE = "unavailable"
    NO_ACTION = "no_action"


@dataclass(frozen=True)
class Route:
    kind: RouteKind
    reason: str | None = None


class CityRouteRegistry:
    def for_artifact(self, artifact: Artifact) -> Route:
        if artifact.availability is not ArtifactAvailability.AVAILABLE:
            return Route(
                RouteKind.UNAVAILABLE, artifact.availability_reason or artifact.availability
            )
        if artifact.media_type in DOCUMENT_MEDIA_TYPES:
            return Route(RouteKind.DOCUMENT)
        if artifact.media_type in MEETING_MEDIA_TYPES:
            return Route(RouteKind.MEDIA)
        return Route(RouteKind.NO_ACTION, f"no City MVP route for {artifact.media_type}")

    def requires_document_extraction(self, artifact: Artifact) -> bool:
        return self.for_artifact(artifact).kind is RouteKind.DOCUMENT

    def requires_media_extraction(self, artifact: Artifact) -> bool:
        return self.for_artifact(artifact).kind is RouteKind.MEDIA

    def is_unavailable(self, artifact: Artifact) -> bool:
        return self.for_artifact(artifact).kind is RouteKind.UNAVAILABLE
