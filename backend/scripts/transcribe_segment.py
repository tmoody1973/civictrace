#!/usr/bin/env python3
"""Transcribe the reviewed focus segment with Speech-to-Text V2 (MOO-716).

Uploads the extracted segment audio to the vault (create-only), runs one batch STT job,
and writes the TranscriptArtifact JSON into the fixture corpus (committed — it is small,
derived from the public record, and carries full provenance).

Usage (from backend/):
  uv run python scripts/transcribe_segment.py --project civictrace-dev-tm
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.transcript import TranscriptArtifact  # noqa: E402
from app.services.corpus import load_corpus_manifest  # noqa: E402
from app.services.transcription import GoogleSttV2Transcriber, estimated_stt_usd  # noqa: E402

FIXTURE_DIR = BACKEND_ROOT / "tests" / "fixtures" / "milwaukee-city-promise-ledger-demo-v1"
AUDIO = FIXTURE_DIR / "media" / "znd-2026-07-28-tid121-segment.flac"
OUT = FIXTURE_DIR / "transcripts" / "znd-2026-07-28-tid121.json"
SOURCE_ARTIFACT = "znd-committee-2026-07-28"


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    from google.cloud import storage

    manifest_path = BACKEND_ROOT.parent / "docs" / "sources" / "corpus-manifest.yaml"
    manifest = load_corpus_manifest(manifest_path)
    media = manifest.media_entry(SOURCE_ARTIFACT)
    assert media.focus_segment is not None
    audio_bytes = AUDIO.read_bytes()
    audio_hash = "sha256:" + hashlib.sha256(audio_bytes).hexdigest()

    bucket = storage.Client(project=args.project).bucket(f"{args.project}-civictrace-vault")
    blob = bucket.blob(AUDIO.name)
    if not blob.exists():
        blob.metadata = {
            "derived_from": SOURCE_ARTIFACT,
            "source_hash": media.content_hash or "",
            "segment": f"{media.focus_segment.start_seconds}-{media.focus_segment.end_seconds}s",
        }
        blob.upload_from_filename(str(AUDIO), if_generation_match=0)
    audio_uri = f"gs://{bucket.name}/{AUDIO.name}"

    transcriber = GoogleSttV2Transcriber(
        project=args.project, output_gcs_prefix=f"gs://{args.project}-civictrace-packets/stt-out"
    )
    segments, diarized = transcriber.transcribe(audio_uri)
    artifact = TranscriptArtifact(
        transcript_id="tr-znd-2026-07-28-tid121",
        source_artifact_id=SOURCE_ARTIFACT,
        segment_start_seconds=media.focus_segment.start_seconds,
        segment_end_seconds=media.focus_segment.end_seconds,
        audio_uri=audio_uri,
        audio_hash=audio_hash,
        stt_provider="google-speech-v2",
        stt_model="latest_long",
        diarization=diarized,
        created_at=datetime.now(UTC),
        segments=segments,
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(artifact.model_dump_json(indent=1))
    speakers = sorted({s.speaker_label for s in segments})
    print(f"{len(segments)} segments · diarized={diarized} · speakers={speakers}")
    print(f"est STT cost: USD {estimated_stt_usd(artifact.duration_seconds())}")
    print(f"→ {OUT.relative_to(BACKEND_ROOT)}")
    return 0 if segments else 1


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
