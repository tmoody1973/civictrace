"""Serve the exact vaulted bytes of one artifact so a reviewer can open the real page.

The path on disk comes from the ledger's own record (storage_uri), never from the request.
# ponytail: reads the whole file into memory; stream when media (Slice 6) arrives.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.core.dependencies import TraceReader
from app.domain.enums import ArtifactAvailability
from app.schemas.api import ApiEnvelope
from app.services.artifact_vault import HASH_PREFIX, sha256_hex
from app.services.uri_bytes import LocalUriResolver

router = APIRouter()
CONTENT_HASH_HEADER = "X-CivicTrace-Content-Hash"

# The viewer renders documents inline. A meeting recording (2.9GB) must never be read
# into API memory — reviewers reach media through its transcript evidence and the
# official source link; the studio's media pane is MOO-718.
MAX_INLINE_SERVE_BYTES = 64 * 1024 * 1024


@router.api_route("/artifacts/{artifact_id}/file", methods=["GET", "HEAD"])
def artifact_file(artifact_id: str, request: Request) -> Response:
    reader: TraceReader = request.app.state.trace_reader
    artifact = reader.artifact(artifact_id)
    if artifact is None:
        return _error(404, f"artifact {artifact_id!r} not found")
    if artifact.availability is not ArtifactAvailability.AVAILABLE or not artifact.storage_uri:
        return _error(404, f"artifact {artifact_id!r} is {artifact.availability.value}")
    too_large = artifact.byte_length is not None and artifact.byte_length > MAX_INLINE_SERVE_BYTES
    if too_large or (artifact.media_type or "").startswith(("video/", "audio/")):
        return _error(
            413,
            f"artifact {artifact_id!r} is meeting media; it is not served inline. "
            "Review its transcript evidence or open the official source.",
        )
    resolver: LocalUriResolver = getattr(
        request.app.state, "uri_resolver", None
    ) or LocalUriResolver()
    payload = resolver.read_bytes(artifact.storage_uri)
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


def _error(status: int, message: str) -> JSONResponse:
    envelope: ApiEnvelope[None] = ApiEnvelope(ok=False, data=None, error=message)
    return JSONResponse(status_code=status, content=envelope.model_dump(mode="json"))
