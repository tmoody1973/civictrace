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
)
from app.schemas.source import SourceEvent
from app.services.artifact_fetch import USER_AGENT, _default_http_get
from app.services.artifact_vault import HASH_PREFIX, sha256_hex

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
    ) -> None:
        self._policy = source_policy
        self._store_bytes = store_bytes
        self._save_manifest = save_manifest
        self._http_get = http_get
        self._clock = clock

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
        for attachment_id in selected_ids:
            attachment = by_id.get(attachment_id)
            if attachment is None:
                raise CaseIntakeError(f"attachment {attachment_id} is not in the bundle")
            self._assert_allowlisted(attachment.url)
            payload = self._http_get(attachment.url)
            if not payload.startswith(b"%PDF"):
                raise CaseIntakeError(
                    f"attachment {attachment_id} at {attachment.url} is not a PDF document; "
                    "only public document evidence may enter a case"
                )
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
        self._save_manifest(manifest)
        events = [
            manifest.source_event(entry.artifact_id)
            for entry in sorted(
                manifest.artifacts, key=lambda e: e.role != "original_commitment"
            )
        ]
        return manifest, events

    def _assert_allowlisted(self, url: str) -> None:
        try:
            self._policy.assert_url_allowed(INTAKE_SOURCE_ID, url)
        except SourcePolicyError as exc:
            raise CaseIntakeError(str(exc)) from exc


def _page_count(payload: bytes) -> int | None:
    try:
        return len(PdfReader(io.BytesIO(payload)).pages)
    except Exception:  # noqa: BLE001  — an unreadable page count is a limitation, not a crash
        return None
