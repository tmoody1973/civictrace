"""Serve the exact vaulted bytes of one artifact so a reviewer can open the real page.

The path on disk comes from the ledger's own record (storage_uri), never from the request.
# ponytail: reads the whole file into memory; stream when media (Slice 6) arrives.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.core.dependencies import TraceReader
from app.domain.enums import ArtifactAvailability
from app.schemas.api import ApiEnvelope
from app.schemas.source import Artifact
from app.services.artifact_vault import HASH_PREFIX, sha256_hex

router = APIRouter()
CONTENT_HASH_HEADER = "X-CivicTrace-Content-Hash"


@router.api_route("/artifacts/{artifact_id}/file", methods=["GET", "HEAD"])
def artifact_file(artifact_id: str, request: Request) -> Response:
    reader: TraceReader = request.app.state.trace_reader
    artifact = reader.artifact(artifact_id)
    if artifact is None:
        return _error(404, f"artifact {artifact_id!r} not found")
    if artifact.availability is not ArtifactAvailability.AVAILABLE or not artifact.storage_uri:
        return _error(404, f"artifact {artifact_id!r} is {artifact.availability.value}")
    payload = _read_vaulted_bytes(artifact)
    if HASH_PREFIX + sha256_hex(payload) != artifact.content_hash:
        return _error(500, f"artifact {artifact_id!r}: vault bytes do not match ledger hash")
    return Response(
        content=payload,
        media_type=artifact.media_type or "application/octet-stream",
        headers={
            "ETag": f'"{artifact.content_hash}"',
            "Cache-Control": "private, max-age=0",
            CONTENT_HASH_HEADER: artifact.content_hash or "",
        },
    )


def _read_vaulted_bytes(artifact: Artifact) -> bytes:
    parsed = urlparse(artifact.storage_uri or "")
    if parsed.scheme != "file":
        raise NotImplementedError(f"storage scheme {parsed.scheme!r} not served locally")
    return Path(unquote(parsed.path)).read_bytes()


def _error(status: int, message: str) -> JSONResponse:
    envelope: ApiEnvelope[None] = ApiEnvelope(ok=False, data=None, error=message)
    return JSONResponse(status_code=status, content=envelope.model_dump(mode="json"))
