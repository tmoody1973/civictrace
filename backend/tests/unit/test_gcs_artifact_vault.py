"""GcsArtifactVault: bytes stored first with provenance metadata; overwrites refused."""

from __future__ import annotations

from typing import Any

import pytest
from google.api_core.exceptions import PreconditionFailed

from app.domain.enums import ArtifactAvailability
from app.domain.errors import ArtifactImmutabilityError
from app.services.corpus import load_corpus_manifest
from app.services.gcs_artifact_vault import GcsArtifactVault
from tests.conftest import MANIFEST_PATH, REPO_ROOT

PLAN = "tid121-project-plan-2024"
MISSING = "tid-annual-report-2025"


class FakeBlob:
    def __init__(self, bucket: FakeBucket, name: str) -> None:
        self._bucket = bucket
        self.name = name
        self.metadata: dict[str, str] | None = None
        self.content_type: str | None = None

    def exists(self) -> bool:
        return self.name in self._bucket.objects

    def upload_from_string(
        self, data: bytes, *, content_type: str | None = None, if_generation_match: int
    ) -> None:
        assert if_generation_match == 0, "vault must always use the create-only precondition"
        if self.name in self._bucket.objects:
            raise PreconditionFailed("object already exists")
        self._bucket.objects[self.name] = data
        self._bucket.metadata[self.name] = dict(self.metadata or {})
        self.content_type = content_type

    def download_as_bytes(self) -> bytes:
        return self._bucket.objects[self.name]


class FakeBucket:
    def __init__(self, name: str) -> None:
        self.name = name
        self.objects: dict[str, bytes] = {}
        self.metadata: dict[str, dict[str, str]] = {}

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(self, name)


class FakeStorageClient:
    def __init__(self) -> None:
        self.buckets: dict[str, FakeBucket] = {}

    def bucket(self, name: str) -> FakeBucket:
        return self.buckets.setdefault(name, FakeBucket(name))


@pytest.fixture()
def vault() -> tuple[GcsArtifactVault, FakeStorageClient]:
    manifest = load_corpus_manifest(MANIFEST_PATH)
    client = FakeStorageClient()
    built = GcsArtifactVault(
        manifest=manifest,
        fixture_root=REPO_ROOT,
        storage_client=client,  # type: ignore[arg-type]
        bucket_name="test-vault",
    )
    return built, client


def test_stores_bytes_with_provenance_metadata(vault: Any) -> None:
    built, client = vault
    manifest = load_corpus_manifest(MANIFEST_PATH)
    artifact = built.fetch_and_store_sync(manifest.source_event(PLAN))
    assert artifact.availability is ArtifactAvailability.AVAILABLE
    assert artifact.storage_uri is not None and artifact.storage_uri.startswith("gs://test-vault/")
    bucket = client.buckets["test-vault"]
    object_name = artifact.storage_uri.removeprefix("gs://test-vault/")
    assert object_name in bucket.objects
    metadata = bucket.metadata[object_name]
    assert metadata["content_hash"] == artifact.content_hash
    assert metadata["canonical_url"] == artifact.canonical_url
    assert metadata["source_id"] == artifact.source_id
    assert "retrieved_at" in metadata


def test_duplicate_store_of_same_bytes_is_a_noop(vault: Any) -> None:
    built, client = vault
    manifest = load_corpus_manifest(MANIFEST_PATH)
    first = built.fetch_and_store_sync(manifest.source_event(PLAN))
    second = built.fetch_and_store_sync(manifest.source_event(PLAN))
    assert first.storage_uri == second.storage_uri
    assert len(client.buckets["test-vault"].objects) == 1


def test_different_bytes_under_same_name_refused(vault: Any) -> None:
    built, client = vault
    manifest = load_corpus_manifest(MANIFEST_PATH)
    artifact = built.fetch_and_store_sync(manifest.source_event(PLAN))
    object_name = artifact.storage_uri.removeprefix("gs://test-vault/")  # type: ignore[union-attr]
    client.buckets["test-vault"].objects[object_name] = b"tampered"
    with pytest.raises(ArtifactImmutabilityError):
        built.fetch_and_store_sync(manifest.source_event(PLAN))


def test_missing_artifact_stays_not_published_and_stores_nothing(vault: Any) -> None:
    built, client = vault
    manifest = load_corpus_manifest(MANIFEST_PATH)
    artifact = built.fetch_and_store_sync(manifest.source_event(MISSING))
    assert artifact.availability is ArtifactAvailability.NOT_PUBLISHED
    assert artifact.storage_uri is None
    assert client.buckets == {} or not client.buckets.get("test-vault", FakeBucket("x")).objects


def _conversion_manifest():
    """A manifest whose first artifact is a labeled Word→PDF conversion (MOO-726)."""
    manifest = load_corpus_manifest(MANIFEST_PATH)
    converted = manifest.artifacts[0].model_copy(
        update={
            "original_content_hash": "sha256:" + "ab" * 32,
            "original_media_type": "application/msword",
            "original_local_path": "records/converted-original.doc",
            "original_byte_length": 123,
        }
    )
    return manifest.model_copy(update={"artifacts": [converted, *manifest.artifacts[1:]]})


def test_conversion_is_verified_present_never_refetched() -> None:
    manifest = _conversion_manifest()
    client = FakeStorageClient()
    entry = manifest.artifacts[0]
    object_name = f"{entry.artifact_id}.pdf"
    client.bucket("test-vault").objects[object_name] = b"%PDF-1.7 vaulted conversion"

    def refuse_fetch(_entry):
        raise AssertionError("a conversion must never be re-fetched from the canonical URL")

    built = GcsArtifactVault(
        manifest=manifest,
        fixture_root=REPO_ROOT,
        storage_client=client,  # type: ignore[arg-type]
        bucket_name="test-vault",
        fetch_bytes=refuse_fetch,
    )
    artifact = built.fetch_and_store_sync(manifest.source_event(entry.artifact_id))
    assert artifact.availability is ArtifactAvailability.AVAILABLE
    assert artifact.storage_uri == f"gs://test-vault/{object_name}"


def test_missing_conversion_fails_closed() -> None:
    manifest = _conversion_manifest()
    built = GcsArtifactVault(
        manifest=manifest,
        fixture_root=REPO_ROOT,
        storage_client=FakeStorageClient(),  # type: ignore[arg-type]
        bucket_name="test-vault",
    )
    entry = manifest.artifacts[0]
    with pytest.raises(ArtifactImmutabilityError, match="converted document missing"):
        built.fetch_and_store_sync(manifest.source_event(entry.artifact_id))
