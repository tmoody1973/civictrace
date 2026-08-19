"""PolicyService for the workflow: source allowlist, artifact integrity, extraction gate."""

from __future__ import annotations

from app.domain.enums import ArtifactAvailability
from app.domain.errors import FixtureIntegrityError
from app.policies.source_policy import SourcePolicy
from app.schemas.case import CaseLinkProposal, DecisionDeltaProposal, ReviewDecision
from app.schemas.evidence import DocumentExtraction, EntityLinkBatch
from app.schemas.source import Artifact, SourceEvent
from app.services.artifact_text import read_page_texts
from app.services.artifact_vault import HASH_PREFIX, sha256_hex
from app.services.validator import ValidationResult, validate_extraction


class CivicTracePolicyService:
    def __init__(self, *, source_policy: SourcePolicy) -> None:
        self._source_policy = source_policy

    def assert_source_event_allowed(self, event: SourceEvent) -> None:
        self._source_policy.assert_source_event_allowed(event)

    def validate_artifact(self, artifact: Artifact) -> None:
        """Stored bytes must still hash to the recorded content_hash."""
        if artifact.availability is not ArtifactAvailability.AVAILABLE:
            return
        assert artifact.storage_uri and artifact.content_hash
        stored = open(artifact.storage_uri.removeprefix("file://"), "rb").read()
        if HASH_PREFIX + sha256_hex(stored) != artifact.content_hash:
            raise FixtureIntegrityError(
                f"{artifact.artifact_id}: stored bytes no longer match hash"
            )

    def validate_document_extraction(
        self, extraction: DocumentExtraction, artifact: Artifact
    ) -> ValidationResult:
        page_texts = (
            read_page_texts(artifact.storage_uri, artifact.media_type)
            if artifact.storage_uri
            else None
        )
        return validate_extraction(extraction, artifact, page_texts)

    def validate_entity_links(self, links: EntityLinkBatch, extraction: DocumentExtraction) -> None:
        return None

    def validate_case_link(self, proposal: CaseLinkProposal) -> None:
        return None

    def validate_delta(self, delta: DecisionDeltaProposal, case_bundle: dict[str, object]) -> None:
        raise NotImplementedError("Slice 2")

    def assert_review_acceptable(self, review: ReviewDecision) -> None:
        raise NotImplementedError("Slice 2")
