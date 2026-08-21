"""PolicyService for the workflow: source allowlist, artifact integrity, extraction gate."""

from __future__ import annotations

from collections.abc import Callable

from app.domain.enums import ArtifactAvailability
from app.domain.errors import FixtureIntegrityError
from app.policies.source_policy import SourcePolicy
from app.schemas.case import CaseBundle, CaseLinkProposal, DecisionDeltaProposal, ReviewDecision
from app.schemas.evidence import DocumentExtraction, EntityLinkBatch, MediaExtraction
from app.schemas.inquiry import InquiryProposal
from app.schemas.source import Artifact, SourceEvent
from app.schemas.transcript import TranscriptArtifact
from app.services.artifact_text import read_page_texts
from app.services.artifact_vault import HASH_PREFIX, sha256_hex
from app.services.uri_bytes import LocalUriResolver
from app.services.validator import (
    ValidationResult,
    validate_delta,
    validate_extraction,
    validate_inquiry,
    validate_media_extraction,
)

# Re-hash stored bytes on every run only up to this size. A meeting video (2.9GB) was
# hash-verified when the operator vaulted it (MOO-715); re-downloading it per replay
# would be pure cost with no new information.
MAX_REHASH_BYTES = 64 * 1024 * 1024


class CivicTracePolicyService:
    def __init__(
        self,
        *,
        source_policy: SourcePolicy,
        uri_resolver: LocalUriResolver | None = None,
        transcript_for: Callable[[str], TranscriptArtifact] | None = None,
    ) -> None:
        self._source_policy = source_policy
        # gs:// URIs work when the cloud services inject a GcsUriResolver (MOO-709).
        self._uri_resolver = uri_resolver or LocalUriResolver()
        self._transcript_for = transcript_for

    def assert_source_event_allowed(self, event: SourceEvent) -> None:
        self._source_policy.assert_source_event_allowed(event)

    def validate_artifact(self, artifact: Artifact) -> None:
        """Stored bytes must still hash to the recorded content_hash."""
        if artifact.availability is not ArtifactAvailability.AVAILABLE:
            return
        assert artifact.storage_uri and artifact.content_hash
        if artifact.byte_length is not None and artifact.byte_length > MAX_REHASH_BYTES:
            return
        stored = self._uri_resolver.read_bytes(artifact.storage_uri)
        if HASH_PREFIX + sha256_hex(stored) != artifact.content_hash:
            raise FixtureIntegrityError(
                f"{artifact.artifact_id}: stored bytes no longer match hash"
            )

    def validate_document_extraction(
        self, extraction: DocumentExtraction, artifact: Artifact
    ) -> ValidationResult:
        page_texts = (
            read_page_texts(
                self._uri_resolver.to_local_path(artifact.storage_uri).as_uri(),
                artifact.media_type,
            )
            if artifact.storage_uri
            else None
        )
        return validate_extraction(extraction, artifact, page_texts)

    def validate_media_extraction(
        self, extraction: MediaExtraction, artifact: Artifact
    ) -> ValidationResult:
        if self._transcript_for is None:
            return ValidationResult(
                (f"{artifact.artifact_id}: no transcript available; media evidence refused",)
            )
        transcript = self._transcript_for(artifact.artifact_id)
        return validate_media_extraction(extraction, artifact, transcript)

    def validate_entity_links(self, links: EntityLinkBatch, extraction: DocumentExtraction) -> None:
        return None

    def validate_case_link(self, proposal: CaseLinkProposal) -> None:
        return None

    def validate_delta(
        self, delta: DecisionDeltaProposal, case_bundle: CaseBundle
    ) -> ValidationResult:
        return validate_delta(delta, case_bundle)

    def review_is_stageable(self, review: ReviewDecision, delta: DecisionDeltaProposal) -> bool:
        """Only an APPROVE with zero blocking issues stages; the reviewer cannot edit the delta."""
        return review.is_stageable() and delta.requires_human_review

    def validate_inquiry(
        self, inquiry: InquiryProposal, case_bundle: CaseBundle
    ) -> ValidationResult:
        return validate_inquiry(inquiry, case_bundle)
