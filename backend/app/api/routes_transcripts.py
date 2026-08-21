"""Serve the committed diarized transcript of a meeting artifact (MOO-718).

The transcript is a reviewed fixture file named by the corpus manifest — never model
output at request time. Anything missing fails closed with a clear message.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.api import ApiEnvelope, TranscriptSegmentView, TranscriptView
from app.schemas.corpus import CorpusManifest
from app.schemas.transcript import TranscriptArtifact
from app.services.corpus import load_corpus_manifest

router = APIRouter()

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent
MANIFEST_PATH = _REPO_ROOT / "docs" / "sources" / "corpus-manifest.yaml"

CONFIDENCE_NOTE = (
    "The transcription model reports no per-word confidence; "
    "verify quotes against the official recording."
)


@lru_cache(maxsize=1)
def _manifest() -> CorpusManifest:
    return load_corpus_manifest(MANIFEST_PATH)


@router.get("/artifacts/{artifact_id}/transcript")
def artifact_transcript(artifact_id: str) -> JSONResponse:
    manifest = _manifest()
    if not manifest.is_media(artifact_id):
        return _error(404, f"artifact {artifact_id!r} has no meeting transcript")
    entry = manifest.media_entry(artifact_id)
    if entry.transcript_path is None:
        return _error(404, f"artifact {artifact_id!r}: no reviewed transcript committed yet")
    transcript_file = _REPO_ROOT / manifest.fixture_dir / entry.transcript_path
    if not transcript_file.exists():
        return _error(404, f"artifact {artifact_id!r}: transcript file missing from the corpus")
    transcript = TranscriptArtifact.model_validate_json(transcript_file.read_text())
    view = TranscriptView(
        transcript_id=transcript.transcript_id,
        artifact_id=transcript.source_artifact_id,
        segment_start_seconds=transcript.segment_start_seconds,
        segment_end_seconds=transcript.segment_end_seconds,
        stt_provider=transcript.stt_provider,
        stt_model=transcript.stt_model,
        diarization=transcript.diarization,
        confidence_note=CONFIDENCE_NOTE,
        segments=[
            TranscriptSegmentView(
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                speaker_label=segment.speaker_label,
                text=segment.text,
                confidence=segment.confidence,
            )
            for segment in transcript.segments
        ],
    )
    envelope: ApiEnvelope[TranscriptView] = ApiEnvelope(ok=True, data=view, error=None)
    return JSONResponse(content=envelope.model_dump(mode="json"))


def _error(status: int, message: str) -> JSONResponse:
    envelope: ApiEnvelope[None] = ApiEnvelope(ok=False, data=None, error=message)
    return JSONResponse(status_code=status, content=envelope.model_dump(mode="json"))
