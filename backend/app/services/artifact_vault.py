"""Immutable raw-artifact vault. The artifact is stored, hashed, and provenance-stamped before any
extraction may run. Slice 1 ships the local fixture implementation only.

# ponytail: GCS implementation (same protocol) lands in Slice 2 behind the ArtifactVault protocol.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.domain.enums import ArtifactAvailability
from app.domain.errors import ArtifactImmutabilityError, FixtureIntegrityError
from app.orchestration.workflow import WorkflowContext
from app.schemas.corpus import CorpusManifest, ManifestArtifact
from app.schemas.source import Artifact, SourceEvent

HASH_PREFIX = "sha256:"


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_verified_fixture(fixture_dir: Path, entry: ManifestArtifact) -> bytes:
    """Read reviewed fixture bytes and refuse them if they no longer match the manifest hash."""
    if entry.local_path is None or entry.content_hash is None:
        raise FixtureIntegrityError(f"{entry.artifact_id}: AVAILABLE entry lacks local_path/hash")
    payload = (fixture_dir / entry.local_path).read_bytes()
    if HASH_PREFIX + sha256_hex(payload) != entry.content_hash:
        raise FixtureIntegrityError(
            f"{entry.artifact_id}: fixture bytes do not match manifest hash"
        )
    return payload


class LocalFixtureVault:
    """Serves artifacts from the reviewed fixture corpus and stores them immutably on local disk."""

    def __init__(self, *, manifest: CorpusManifest, fixture_root: Path, vault_dir: Path) -> None:
        self._manifest = manifest
        self._fixture_dir = fixture_root / manifest.fixture_dir
        self._vault_dir = vault_dir

    async def fetch_and_store(self, event: SourceEvent, *, context: WorkflowContext) -> Artifact:
        return self.fetch_and_store_sync(event)

    def fetch_and_store_sync(self, event: SourceEvent) -> Artifact:
        entry = self._manifest.entry(event.artifact_id)
        if entry.availability is not ArtifactAvailability.AVAILABLE:
            return _unavailable_artifact(entry)
        if self._manifest.is_media(entry.artifact_id):
            return self._verify_media_present(entry)
        payload = self._read_verified_fixture(entry)
        stored_path = self._store_immutably(entry, payload)
        return _available_artifact(entry, stored_path.resolve().as_uri())

    def _verify_media_present(self, entry: ManifestArtifact) -> Artifact:
        """Meeting media entered the vault via the operator machine (MOO-715) and was
        hash-verified then; here we only confirm a reviewed copy is reachable.
        Re-reading gigabytes per replay would add cost, not information.

        The full recording is too large to commit, so CI machines do not have it. There
        the committed transcript's vaulted-audio URI stands in: it names real preserved
        segment bytes (with a recorded hash) in the immutable cloud vault."""
        assert entry.local_path is not None
        media_path = self._fixture_dir / entry.local_path
        if media_path.exists():
            if entry.byte_length is not None and media_path.stat().st_size != entry.byte_length:
                raise FixtureIntegrityError(
                    f"{entry.artifact_id}: media byte length differs from the manifest"
                )
            return _available_artifact(entry, media_path.resolve().as_uri())
        if entry.transcript_path is not None:
            transcript = json.loads((self._fixture_dir / entry.transcript_path).read_text())
            return _available_artifact(entry, str(transcript["audio_uri"]))
        raise FixtureIntegrityError(
            f"{entry.artifact_id}: no reviewed media copy and no committed transcript"
        )

    def _read_verified_fixture(self, entry: ManifestArtifact) -> bytes:
        return read_verified_fixture(self._fixture_dir, entry)

    def _store_immutably(self, entry: ManifestArtifact, payload: bytes) -> Path:
        assert entry.local_path is not None
        target = self._vault_dir / f"{entry.artifact_id}{Path(entry.local_path).suffix}"
        if target.exists():
            if sha256_hex(target.read_bytes()) != sha256_hex(payload):
                raise ArtifactImmutabilityError(
                    f"{entry.artifact_id}: stored bytes differ; refusing to overwrite"
                )
            return target
        self._vault_dir.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(payload)
        return target


def _available_artifact(entry: ManifestArtifact, storage_uri: str) -> Artifact:
    return Artifact(
        artifact_id=entry.artifact_id,
        source_id=entry.source_id,
        canonical_url=entry.canonical_url,
        external_id=entry.external_id,
        title=entry.title,
        media_type=entry.media_type,
        content_hash=entry.content_hash,
        byte_length=entry.byte_length,
        page_count=entry.page_count,
        storage_uri=storage_uri,
        retrieved_at=entry.retrieved_at,
        availability=ArtifactAvailability.AVAILABLE,
    )


def _unavailable_artifact(entry: ManifestArtifact) -> Artifact:
    return Artifact(
        artifact_id=entry.artifact_id,
        source_id=entry.source_id,
        canonical_url=entry.canonical_url,
        external_id=entry.external_id,
        title=entry.title,
        media_type=None,
        content_hash=None,
        byte_length=None,
        page_count=None,
        storage_uri=None,
        retrieved_at=entry.retrieved_at,
        availability=entry.availability,
        availability_reason=entry.availability_reason,
    )
