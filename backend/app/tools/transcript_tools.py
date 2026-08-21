"""The Media Evidence Agent's only tool: read spans of ONE committed transcript.

The tool object is bound to a single media artifact id and transcript at construction time
by deterministic code. The model cannot name another artifact or path — a wrong id gets a
refusal string, never text. Reads are capped at MAX_SPAN_MS_PER_CALL per call.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.transcript import TranscriptArtifact, TranscriptSegment

MAX_SPAN_MS_PER_CALL = 300_000  # 5 minutes of speech per read


def segments_overlapping(
    transcript: TranscriptArtifact, start_ms: int, end_ms: int
) -> list[TranscriptSegment]:
    return [
        segment
        for segment in transcript.segments
        if segment.start_ms < end_ms and segment.end_ms > start_ms
    ]


@dataclass
class TranscriptSpanReader:
    """Read-only, single-transcript span reader. `name` satisfies the ReadOnlyTool protocol."""

    artifact_id: str
    transcript: TranscriptArtifact
    name: str = "read_transcript_span"
    calls: int = field(default=0)

    @property
    def duration_ms(self) -> int:
        return self.transcript.duration_seconds() * 1000

    def read_transcript_span(self, artifact_id: str, start_ms: int, end_ms: int) -> str:
        """Return transcript segments overlapping start_ms..end_ms of the meeting segment.

        Args:
            artifact_id: must be the media artifact this task is about; any other id is refused.
            start_ms: span start in milliseconds, relative to the transcribed segment (0-based).
            end_ms: span end in milliseconds; at most 300000 ms (5 minutes) per call.
        """
        self.calls += 1
        if artifact_id != self.artifact_id:
            return (
                f"REFUSED: this task may only read the transcript of {self.artifact_id!r}; "
                f"{artifact_id!r} is outside its boundary."
            )
        if start_ms < 0 or end_ms <= start_ms:
            return "REFUSED: times are 0-based milliseconds and end_ms must be > start_ms."
        if end_ms - start_ms > MAX_SPAN_MS_PER_CALL:
            return f"REFUSED: at most {MAX_SPAN_MS_PER_CALL} ms per call; narrow the span."
        total = self.duration_ms
        if start_ms >= total:
            return f"REFUSED: the transcript ends at {total} ms; {start_ms} does not exist."
        segments = segments_overlapping(self.transcript, start_ms, end_ms)
        if not segments:
            return f"No transcript segments between {start_ms} and {end_ms} ms."
        lines = [
            f"[{segment.start_ms}-{segment.end_ms} ms] {segment.speaker_label}: {segment.text}"
            for segment in segments
        ]
        return "\n".join(lines)
