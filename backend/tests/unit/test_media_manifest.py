"""The reviewed media fixture entry (Slice 6, MOO-715): real manifest, real bounds."""

from __future__ import annotations

from pathlib import Path

from app.services.corpus import load_corpus_manifest

MANIFEST = Path(__file__).parents[3] / "docs" / "sources" / "corpus-manifest.yaml"


def test_media_entry_is_separate_from_the_document_replay_list() -> None:
    manifest = load_corpus_manifest(MANIFEST)
    document_ids = {entry.artifact_id for entry in manifest.artifacts}
    assert "znd-committee-2026-07-28" not in document_ids  # replay path untouched
    entry = manifest.media_entry("znd-committee-2026-07-28")
    assert entry.media_type == "video/mp4"
    assert entry.granicus_clip_id == 5262
    assert entry.legistar_event_id == 13443
    assert entry.content_hash is not None and entry.content_hash.startswith("sha256:")


def test_focus_segment_bounds_come_from_legistar_video_indexes() -> None:
    entry = load_corpus_manifest(MANIFEST).media_entry("znd-committee-2026-07-28")
    segment = entry.focus_segment
    assert segment is not None
    assert (segment.start_seconds, segment.end_seconds) == (5287, 5990)
    assert segment.end_seconds <= (entry.duration_seconds or 0)
    assert "EventItemVideoIndex" in segment.basis  # bounds are official, not guessed
