"""GET /artifacts/{id}/transcript serves the committed diarized transcript (MOO-718)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.dependencies import InMemoryTraceReader
from app.main import create_app

MEDIA_ID = "znd-committee-2026-07-28"


def _client() -> TestClient:
    return TestClient(create_app(trace_reader=InMemoryTraceReader("case", [])))


def test_meeting_transcript_is_served_with_segments_and_labels() -> None:
    response = _client().get(f"/artifacts/{MEDIA_ID}/transcript")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["artifact_id"] == MEDIA_ID
    assert data["segment_start_seconds"] == 5287
    assert len(data["segments"]) == 42
    first = data["segments"][0]
    assert first["speaker_label"].startswith("SPEAKER_")
    # chirp_3 reports no per-word confidence; the API must say so, never hide it
    assert first["confidence"] is None
    assert "confidence" in data["confidence_note"]


def test_document_artifact_has_no_transcript() -> None:
    response = _client().get("/artifacts/tid121-project-plan-2024/transcript")
    assert response.status_code == 404
    assert "no meeting transcript" in response.json()["error"]


def test_unknown_artifact_is_404_envelope() -> None:
    response = _client().get("/artifacts/nope/transcript")
    assert response.status_code == 404
    assert response.json()["ok"] is False
