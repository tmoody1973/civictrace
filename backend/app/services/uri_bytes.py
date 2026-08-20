"""Resolve a ledger storage_uri (file:// or gs://) to verified local bytes.

One seam used by the policy hash check, the page-text reader, the artifact file
route, and the cloud packet reader. gs:// objects are downloaded once into a
cache directory; the callers keep working on plain local paths.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlparse


class BlobReader(Protocol):
    def download_as_bytes(self) -> bytes: ...


class BucketReader(Protocol):
    def blob(self, name: str) -> BlobReader: ...


class StorageReader(Protocol):
    def bucket(self, name: str) -> BucketReader: ...


class LocalUriResolver:
    """file:// only. The default everywhere outside the cloud services."""

    def to_local_path(self, storage_uri: str) -> Path:
        parsed = urlparse(storage_uri)
        if parsed.scheme != "file":
            raise ValueError(f"storage scheme {parsed.scheme!r} is not readable here")
        return Path(unquote(parsed.path))

    def read_bytes(self, storage_uri: str) -> bytes:
        return self.to_local_path(storage_uri).read_bytes()


class GcsUriResolver(LocalUriResolver):
    """gs:// downloads once into a cache dir; file:// passes through unchanged."""

    def __init__(self, storage_client: StorageReader, cache_dir: Path | None = None) -> None:
        self._client = storage_client
        self._cache_dir = cache_dir or Path(tempfile.gettempdir()) / "civictrace-artifact-cache"

    def to_local_path(self, storage_uri: str) -> Path:
        parsed = urlparse(storage_uri)
        if parsed.scheme != "gs":
            return super().to_local_path(storage_uri)
        object_name = parsed.path.lstrip("/")
        cached = self._cache_dir / parsed.netloc / object_name
        if not cached.exists():
            payload = self._client.bucket(parsed.netloc).blob(object_name).download_as_bytes()
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(payload)
        return cached

    def read_bytes(self, storage_uri: str) -> bytes:
        return self.to_local_path(storage_uri).read_bytes()
