"""Turn one approved candidate bundle into a live case (MOO-719).

Deterministic code only: allowlist check → canonical fetch → hash-lock → immutable vault
write → manifest-equivalent record. Any failure marks the bundle FAILED with the reason;
a bundle that is not APPROVED by a named human can never reach this code's happy path.
"""

from __future__ import annotations

import io
import logging
from collections.abc import Callable
from datetime import datetime

from pypdf import PdfReader

from app.domain.errors import SourcePolicyError
from app.policies.source_policy import SourcePolicy
from app.schemas.corpus import CorpusManifest, ManifestArtifact
from app.schemas.intake import (
    INTAKE_SOURCE_ID,
    BundleStatus,
    CandidateBundle,
    FetchedAttachment,
    IntakeSelection,
    build_intake_manifest,
    intake_corpus_id,
)
from app.schemas.source import SourceEvent
from app.services.artifact_fetch import USER_AGENT, _default_http_get
from app.services.artifact_vault import HASH_PREFIX, sha256_hex
from app.services.office_convert import (
    ConversionError,
    classify_attachment,
    convert_word_to_pdf,
    word_media_type,
    word_suffix,
)

logger = logging.getLogger("civictrace.intake")

__all__ = ["CaseIntakeError", "CaseIntakeService", "USER_AGENT"]


class CaseIntakeError(Exception):
    """The bundle could not become a case; the reason is user-showable."""


class CaseIntakeService:
    def __init__(
        self,
        *,
        source_policy: SourcePolicy,
        store_bytes: Callable[[ManifestArtifact, bytes], str],
        save_manifest: Callable[[CorpusManifest], None],
        http_get: Callable[[str], bytes] = _default_http_get,
        clock: Callable[[], datetime],
        convert_to_pdf: Callable[[bytes], bytes] = convert_word_to_pdf,
        load_vaulted_pdf: Callable[[str], bytes | None] = lambda object_name: None,
    ) -> None:
        self._policy = source_policy
        self._store_bytes = store_bytes
        self._save_manifest = save_manifest
        self._http_get = http_get
        self._clock = clock
        self._convert_to_pdf = convert_to_pdf
        # LibreOffice output is not byte-identical across runs; a Cloud Tasks retry must
        # adopt the conversion already in the immutable vault instead of re-converting.
        self._load_vaulted_pdf = load_vaulted_pdf

    def create_case(
        self, bundle: CandidateBundle, selection: IntakeSelection
    ) -> tuple[CorpusManifest, list[SourceEvent]]:
        """Approved bundle + human roles → vaulted artifacts + persisted case recipe.

        Returns the manifest and its ordered source events (promise documents first),
        ready for the replay pipeline. Raises CaseIntakeError on any refusal.
        """
        # DRAFT = no human approval yet; CASE_CREATED = already done. CREATING/FAILED are
        # legitimate retry states — a crash after approval must not un-approve the bundle.
        if bundle.status in (BundleStatus.DRAFT, BundleStatus.CASE_CREATED):
            raise CaseIntakeError(
                f"bundle {bundle.bundle_id} is {bundle.status}; only an approved, uncreated "
                "bundle may become a case"
            )
        selected_ids = [*selection.promise_attachment_ids, *selection.later_attachment_ids]
        by_id = {attachment.attachment_id: attachment for attachment in bundle.attachments}
        fetched: dict[int, FetchedAttachment] = {}
        payloads: dict[int, bytes] = {}
        originals: dict[int, bytes] = {}
        for attachment_id in selected_ids:
            attachment = by_id.get(attachment_id)
            if attachment is None:
                raise CaseIntakeError(f"attachment {attachment_id} is not in the bundle")
            self._assert_allowlisted(attachment.url)
            payload = self._http_get(attachment.url)
            kind = classify_attachment(payload, attachment.url)
            if kind == "unsupported":
                raise CaseIntakeError(
                    f"attachment {attachment_id} at {attachment.url} is not a PDF or Word "
                    "document; this format cannot become case evidence yet"
                )
            if kind == "word":
                originals[attachment_id] = payload
                converted = self._conversion_for(bundle, attachment_id, payload)
                payloads[attachment_id] = converted
                fetched[attachment_id] = FetchedAttachment(
                    attachment_id=attachment_id,
                    content_hash=HASH_PREFIX + sha256_hex(converted),
                    byte_length=len(converted),
                    page_count=_page_count(converted),
                    original_content_hash=HASH_PREFIX + sha256_hex(payload),
                    original_media_type=word_media_type(payload),
                    original_byte_length=len(payload),
                    original_suffix=word_suffix(payload),
                )
                continue
            payloads[attachment_id] = payload
            fetched[attachment_id] = FetchedAttachment(
                attachment_id=attachment_id,
                content_hash=HASH_PREFIX + sha256_hex(payload),
                byte_length=len(payload),
                page_count=_page_count(payload),
            )
        try:
            manifest = build_intake_manifest(
                bundle, selection, fetched, retrieved_at=self._clock()
            )
        except ValueError as exc:
            raise CaseIntakeError(str(exc)) from exc
        for entry in manifest.artifacts:
            assert entry.legistar_attachment_id is not None
            storage_uri = self._store_bytes(entry, payloads[entry.legistar_attachment_id])
            logger.info("intake vaulted %s at %s", entry.artifact_id, storage_uri)
            if entry.original_local_path is not None:
                original_uri = self._store_bytes(
                    _original_entry(entry), originals[entry.legistar_attachment_id]
                )
                logger.info(
                    "intake vaulted canonical original of %s at %s",
                    entry.artifact_id,
                    original_uri,
                )
        self._save_manifest(manifest)
        events = [
            manifest.source_event(entry.artifact_id)
            for entry in sorted(
                manifest.artifacts, key=lambda e: e.role != "original_commitment"
            )
        ]
        return manifest, events

    def _conversion_for(
        self, bundle: CandidateBundle, attachment_id: int, original: bytes
    ) -> bytes:
        """The vault's existing conversion wins on retry; otherwise convert now."""
        object_name = f"{intake_corpus_id(bundle.legistar_file)}-att{attachment_id}.pdf"
        existing = self._load_vaulted_pdf(object_name)
        if existing is not None:
            logger.info("intake adopting already-vaulted conversion %s", object_name)
            return existing
        try:
            return self._convert_to_pdf(original)
        except ConversionError as exc:
            raise CaseIntakeError(f"attachment {attachment_id}: {exc}") from exc

    def _assert_allowlisted(self, url: str) -> None:
        try:
            self._policy.assert_url_allowed(INTAKE_SOURCE_ID, url)
        except SourcePolicyError as exc:
            raise CaseIntakeError(str(exc)) from exc


def _original_entry(entry: ManifestArtifact) -> ManifestArtifact:
    """The canonical Word bytes get their own vault object under the same artifact id."""
    return entry.model_copy(
        update={
            "content_hash": entry.original_content_hash,
            "media_type": entry.original_media_type,
            "local_path": entry.original_local_path,
            "byte_length": entry.original_byte_length,
            "page_count": None,
            "original_content_hash": None,
            "original_media_type": None,
            "original_local_path": None,
            "original_byte_length": None,
        }
    )


def _page_count(payload: bytes) -> int | None:
    try:
        return len(PdfReader(io.BytesIO(payload)).pages)
    except Exception:  # noqa: BLE001  — an unreadable page count is a limitation, not a crash
        return None
