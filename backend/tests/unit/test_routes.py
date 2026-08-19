from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import ArtifactAvailability
from app.orchestration.routes import CityRouteRegistry, RouteKind
from app.schemas.source import Artifact

NOW = datetime(2026, 8, 19, tzinfo=UTC)


def _artifact(media_type: str | None, availability: ArtifactAvailability) -> Artifact:
    available = availability is ArtifactAvailability.AVAILABLE
    return Artifact(
        artifact_id="a",
        source_id="milwaukee_legistar",
        canonical_url="https://milwaukee.legistar1.com/x" if available else None,
        external_id="x",
        title=None,
        media_type=media_type if available else None,
        content_hash="sha256:0" if available else None,
        byte_length=None,
        page_count=None,
        storage_uri="file:///v/a" if available else None,
        retrieved_at=NOW,
        availability=availability,
        availability_reason=None if available else "not in Legistar as of 2026-08-19",
    )


def test_pdf_routes_to_document_agent() -> None:
    registry = CityRouteRegistry()
    artifact = _artifact("application/pdf", ArtifactAvailability.AVAILABLE)
    assert registry.for_artifact(artifact).kind is RouteKind.DOCUMENT
    assert registry.requires_document_extraction(artifact) is True
    assert registry.is_unavailable(artifact) is False


def test_html_routes_to_document_agent() -> None:
    artifact = _artifact("text/html", ArtifactAvailability.AVAILABLE)
    assert CityRouteRegistry().for_artifact(artifact).kind is RouteKind.DOCUMENT


def test_not_published_is_unavailable_with_reason() -> None:
    registry = CityRouteRegistry()
    artifact = _artifact(None, ArtifactAvailability.NOT_PUBLISHED)
    route = registry.for_artifact(artifact)
    assert route.kind is RouteKind.UNAVAILABLE
    assert route.reason and "2026-08-19" in route.reason
    assert registry.is_unavailable(artifact) is True
    assert registry.requires_document_extraction(artifact) is False


def test_unknown_media_type_is_no_action() -> None:
    artifact = _artifact("audio/mpeg", ArtifactAvailability.AVAILABLE)
    route = CityRouteRegistry().for_artifact(artifact)
    assert route.kind is RouteKind.NO_ACTION
    assert CityRouteRegistry().requires_document_extraction(artifact) is False
