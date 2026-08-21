"""Meeting transcript artifacts (Slice 6.2, MOO-716). Pure: pydantic + stdlib.

A diarization label ("SPEAKER_1") is a label, never a person's identity — naming is a
separate, confidence-gated step that this schema deliberately cannot express. Low
confidence is preserved, never smoothed away.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TranscriptSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_ms: int
    end_ms: int
    speaker_label: str
    text: str
    confidence: float | None = None


class TranscriptArtifact(BaseModel):
    """One transcribed, bounded segment of a vaulted meeting recording."""

    model_config = ConfigDict(extra="forbid")

    transcript_id: str
    source_artifact_id: str
    segment_start_seconds: int
    segment_end_seconds: int
    audio_uri: str
    audio_hash: str
    stt_provider: str
    stt_model: str
    diarization: bool
    created_at: datetime
    segments: list[TranscriptSegment] = Field(default_factory=list)

    def duration_seconds(self) -> int:
        return self.segment_end_seconds - self.segment_start_seconds
