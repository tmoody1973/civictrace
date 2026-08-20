"""Where a rendered DRAFT packet's bytes land: local dir (dev) or the packets bucket (cloud).

The renderer decides the filename and content; the store only persists and returns the
address that goes into the PACKET_RENDERED ledger row.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.services.gcs_artifact_vault import StorageClient


class PacketWriter(Protocol):
    def write(self, filename: str, content: str) -> str:
        """Persist and return the address (local path or gs:// URI)."""
        ...


class LocalPacketWriter:
    def __init__(self, out_dir: Path) -> None:
        self._out_dir = out_dir

    def write(self, filename: str, content: str) -> str:
        self._out_dir.mkdir(parents=True, exist_ok=True)
        target = self._out_dir / filename
        target.write_text(content)
        return str(target)


class GcsPacketWriter:
    """Idempotent by construction: the filename embeds the content hash, so a rerender
    of identical bytes writes the same object."""

    def __init__(self, storage_client: StorageClient, bucket_name: str) -> None:
        self._client = storage_client
        self._bucket_name = bucket_name

    def write(self, filename: str, content: str) -> str:
        blob = self._client.bucket(self._bucket_name).blob(filename)
        if not blob.exists():
            blob.upload_from_string(
                content.encode("utf-8"), content_type="text/markdown", if_generation_match=0
            )
        return f"gs://{self._bucket_name}/{filename}"
