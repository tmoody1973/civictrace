"""Live canonical-source fetcher: allowlist + hash gates, no network (MOO-714)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.policies.source_policy import SourcePolicy
from app.schemas.corpus import ManifestArtifact
from app.services.artifact_fetch import LiveFetchError, LiveSourceFetcher

ALLOWLIST = Path(__file__).parents[3] / "docs" / "sources" / "source-allowlist.yaml"
PAYLOAD = b"%PDF-1.4 reviewed public record bytes"


def _entry(url: str | None, content_hash: str | None) -> ManifestArtifact:
    return ManifestArtifact.model_validate(
        {
            "artifact_id": "tid121-project-plan-2024",
            "role": "original_commitment",
            "source_id": "milwaukee_legistar",
            "canonical_url": url,
            "external_id": "240382/attachment/223678",
            "title": "Project Plan",
            "retrieved_at": "2026-08-19T13:35:00Z",
            "content_hash": content_hash,
            "media_type": "application/pdf",
            "local_path": "records/tid121-project-plan-2024.pdf",
            "availability": "AVAILABLE",
        }
    )


def _fetcher(payload: bytes = PAYLOAD) -> LiveSourceFetcher:
    return LiveSourceFetcher(
        source_policy=SourcePolicy.from_yaml(ALLOWLIST), http_get=lambda url: payload
    )


GOOD_HASH = "sha256:" + hashlib.sha256(PAYLOAD).hexdigest()
GOOD_URL = "https://milwaukee.legistar1.com/milwaukee/attachments/abc.pdf"


def test_fetch_returns_bytes_when_domain_and_hash_match() -> None:
    assert _fetcher().fetch(_entry(GOOD_URL, GOOD_HASH)) == PAYLOAD


def test_fetch_refuses_domain_off_the_allowlist() -> None:
    with pytest.raises(LiveFetchError, match="not allowlisted|not allowed"):
        _fetcher().fetch(_entry("https://evil.example.com/fake.pdf", GOOD_HASH))


def test_fetch_refuses_plain_http() -> None:
    with pytest.raises(LiveFetchError):
        _fetcher().fetch(_entry(GOOD_URL.replace("https://", "http://"), GOOD_HASH))


def test_fetch_refuses_changed_bytes() -> None:
    with pytest.raises(LiveFetchError, match="do not match the reviewed manifest hash"):
        _fetcher(payload=b"tampered").fetch(_entry(GOOD_URL, GOOD_HASH))


def test_fetch_refuses_entry_without_canonical_url() -> None:
    with pytest.raises(LiveFetchError, match="no canonical_url"):
        _fetcher().fetch(_entry(None, GOOD_HASH))
