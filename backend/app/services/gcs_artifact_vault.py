"""GCS-backed immutable artifact vault (Slice 5.2, MOO-708).

Same contract as LocalFixtureVault: reviewed fixture bytes are verified against the
manifest hash, stored bytes-first with provenance metadata, and never overwritten.
Immutability is enforced by GCS itself via the create-only precondition
(`if_generation_match=0`), not by a check that could race.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from google.api_core.exceptions import PreconditionFailed

from app.domain.enums import ArtifactAvailability
from app.domain.errors import ArtifactImmutabilityError
from app.orchestration.workflow import WorkflowContext
from app.schemas.corpus import CorpusManifest, ManifestArtifact
from app.schemas.source import Artifact, SourceEvent
from app.services.artifact_vault import (
    _available_artifact,
    _unavailable_artifact,
    read_verified_fixture,
    sha256_hex,
)


class StorageBlob(Protocol):
    metadata: dict[str, str] | None

    def exists(self) -> bool: ...
    def upload_from_string(
        self, data: bytes, *, content_type: str | None = None, if_generation_match: int
    ) -> None: ...
    def download_as_bytes(self) -> bytes: ...


class StorageBucket(Protocol):
    def blob(self, name: str) -> StorageBlob: ...


class StorageClient(Protocol):
    def bucket(self, name: str) -> StorageBucket: ...


class GcsArtifactVault:
    def __init__(
        self,
        *,
        manifest: CorpusManifest,
        fixture_root: Path,
        storage_client: StorageClient,
        bucket_name: str,
    ) -> None:
        self._manifest = manifest
        self._fixture_dir = fixture_root / manifest.fixture_dir
        self._client = storage_client
        self._bucket_name = bucket_name

    async def fetch_and_store(self, event: SourceEvent, *, context: WorkflowContext) -> Artifact:
        return self.fetch_and_store_sync(event)

    def fetch_and_store_sync(self, event: SourceEvent) -> Artifact:
        entry = self._manifest.entry(event.artifact_id)
        if entry.availability is not ArtifactAvailability.AVAILABLE:
            return _unavailable_artifact(entry)
        payload = read_verified_fixture(self._fixture_dir, entry)
        storage_uri = self._store_immutably(entry, payload)
        return _available_artifact(entry, storage_uri)

    def _store_immutably(self, entry: ManifestArtifact, payload: bytes) -> str:
        assert entry.local_path is not None
        object_name = f"{entry.artifact_id}{Path(entry.local_path).suffix}"
        blob = self._client.bucket(self._bucket_name).blob(object_name)
        blob.metadata = _provenance_metadata(entry)
        try:
            blob.upload_from_string(
                payload, content_type=entry.media_type, if_generation_match=0
            )
        except PreconditionFailed:
            existing = blob.download_as_bytes()
            if sha256_hex(existing) != sha256_hex(payload):
                raise ArtifactImmutabilityError(
                    f"{entry.artifact_id}: stored bytes differ; refusing to overwrite"
                ) from None
        return f"gs://{self._bucket_name}/{object_name}"


def _provenance_metadata(entry: ManifestArtifact) -> dict[str, str]:
    return {
        "artifact_id": entry.artifact_id,
        "source_id": entry.source_id,
        "canonical_url": entry.canonical_url or "",
        "external_id": entry.external_id,
        "content_hash": entry.content_hash or "",
        "media_type": entry.media_type or "",
        "retrieved_at": entry.retrieved_at.isoformat(),
    }
