"""Raw artifacts are stored immutably, with provenance, before anything else may run."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.domain.enums import ArtifactAvailability
from app.domain.errors import ArtifactImmutabilityError, FixtureIntegrityError
from app.schemas.corpus import CorpusManifest
from app.services.artifact_vault import LocalFixtureVault
from app.services.corpus import load_corpus_manifest
from tests.conftest import MANIFEST_PATH, REPO_ROOT

PLAN_ID = "tid121-project-plan-2024"
MISSING_ID = "tid-annual-report-2025"
PLAN_SHA = "7097a1ba6af1fc2aaa60a1d3e9a2b366d63ab067a8e6b4e052b46e8400aaefe1"


@pytest.fixture(scope="module")
def manifest() -> CorpusManifest:
    return load_corpus_manifest(MANIFEST_PATH)


@pytest.fixture
def vault(manifest: CorpusManifest, tmp_path: Path) -> LocalFixtureVault:
    return LocalFixtureVault(
        manifest=manifest, fixture_root=REPO_ROOT, vault_dir=tmp_path / "vault"
    )


def test_manifest_loads_four_artifacts(manifest: CorpusManifest) -> None:
    assert manifest.case_id == "case-tid121-bronzeville-arts-tech-hub"
    assert [entry.artifact_id for entry in manifest.artifacts] == [
        PLAN_ID,
        "tid-annual-report-2024",
        "tid121-amendment-1-2026",
        MISSING_ID,
    ]


def test_store_returns_artifact_with_provenance(
    vault: LocalFixtureVault, manifest: CorpusManifest
) -> None:
    artifact = vault.fetch_and_store_sync(manifest.source_event(PLAN_ID))
    assert artifact.availability is ArtifactAvailability.AVAILABLE
    assert artifact.content_hash == f"sha256:{PLAN_SHA}"
    assert artifact.canonical_url and artifact.canonical_url.startswith(
        "https://milwaukee.legistar1.com/"
    )
    assert artifact.external_id == "240382/attachment/223678"
    assert artifact.media_type == "application/pdf"
    assert artifact.page_count == 31
    assert artifact.storage_uri and artifact.storage_uri.startswith("file://")


def test_stored_bytes_hash_matches_artifact(
    vault: LocalFixtureVault, manifest: CorpusManifest
) -> None:
    artifact = vault.fetch_and_store_sync(manifest.source_event(PLAN_ID))
    stored = Path(artifact.storage_uri.removeprefix("file://"))  # type: ignore[union-attr]
    assert stored.exists()
    assert hashlib.sha256(stored.read_bytes()).hexdigest() == PLAN_SHA


def test_second_store_of_same_bytes_is_noop(
    vault: LocalFixtureVault, manifest: CorpusManifest
) -> None:
    first = vault.fetch_and_store_sync(manifest.source_event(PLAN_ID))
    stored = Path(first.storage_uri.removeprefix("file://"))  # type: ignore[union-attr]
    mtime_before = stored.stat().st_mtime_ns
    second = vault.fetch_and_store_sync(manifest.source_event(PLAN_ID))
    assert second == first
    assert stored.stat().st_mtime_ns == mtime_before


def test_different_bytes_for_same_artifact_id_is_rejected(
    vault: LocalFixtureVault, manifest: CorpusManifest, tmp_path: Path
) -> None:
    first = vault.fetch_and_store_sync(manifest.source_event(PLAN_ID))
    stored = Path(first.storage_uri.removeprefix("file://"))  # type: ignore[union-attr]
    stored.write_bytes(b"%PDF-1.4 tampered")
    with pytest.raises(ArtifactImmutabilityError):
        vault.fetch_and_store_sync(manifest.source_event(PLAN_ID))
    assert stored.read_bytes() == b"%PDF-1.4 tampered", "vault must never overwrite"


def test_missing_record_yields_not_published_without_exception(
    vault: LocalFixtureVault, manifest: CorpusManifest, tmp_path: Path
) -> None:
    artifact = vault.fetch_and_store_sync(manifest.source_event(MISSING_ID))
    assert artifact.availability is ArtifactAvailability.NOT_PUBLISHED
    assert artifact.content_hash is None
    assert artifact.storage_uri is None
    assert artifact.availability_reason and "2025" in artifact.availability_reason
    assert not list((tmp_path / "vault").glob("*")), "nothing is written for a missing record"


def test_fixture_hash_mismatch_fails_loud(manifest: CorpusManifest, tmp_path: Path) -> None:
    tampered_entry = manifest.entry(PLAN_ID).model_copy(
        update={"content_hash": "sha256:" + "0" * 64}
    )
    tampered = manifest.model_copy(update={"artifacts": [tampered_entry]})
    vault = LocalFixtureVault(manifest=tampered, fixture_root=REPO_ROOT, vault_dir=tmp_path / "v")
    with pytest.raises(FixtureIntegrityError):
        vault.fetch_and_store_sync(tampered.source_event(PLAN_ID))


def test_unknown_artifact_id_is_an_error(
    vault: LocalFixtureVault, manifest: CorpusManifest
) -> None:
    event = manifest.source_event(PLAN_ID).model_copy(update={"artifact_id": "not-in-corpus"})
    with pytest.raises(KeyError):
        vault.fetch_and_store_sync(event)
