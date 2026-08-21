"""Speech-to-Text V2 batch transcription behind a seam (Slice 6.2, MOO-716).

The non-deterministic boundary of the media pipeline. `GoogleSttV2Transcriber` runs one
batch job over a vaulted audio URI; parsing is a pure function unit-tested without the
network. Diarization is requested; if the model/region refuses it, we transcribe without
it and say so in the artifact (`diarization=false`) rather than failing or pretending.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from app.schemas.transcript import TranscriptSegment

logger = logging.getLogger("civictrace.transcription")

# Word-level speaker labels arrive as ints or strings depending on path; normalize.
SPEAKER_PREFIX = "SPEAKER_"
STT_USD_PER_MINUTE = 0.016  # V2 dynamic batch list price; the bill is authoritative.


class Transcriber(Protocol):
    def transcribe(self, audio_uri: str) -> tuple[list[TranscriptSegment], bool]:
        """Return (segments, diarization_used)."""
        ...


def segments_from_batch_words(words: list[dict[str, Any]]) -> list[TranscriptSegment]:
    """Group word timings into utterance segments, splitting on speaker change.

    Each word dict: {"word", "start_ms", "end_ms", "speaker" (str|None), "confidence"}.
    A None speaker groups into SPEAKER_UNKNOWN — preserved, not dropped.
    """
    segments: list[TranscriptSegment] = []
    current: list[dict[str, Any]] = []

    def flush() -> None:
        if not current:
            return
        confidences = [w["confidence"] for w in current if w.get("confidence") is not None]
        segments.append(
            TranscriptSegment(
                start_ms=current[0]["start_ms"],
                end_ms=current[-1]["end_ms"],
                speaker_label=_label(current[0].get("speaker")),
                text=" ".join(w["word"] for w in current).strip(),
                confidence=min(confidences) if confidences else None,
            )
        )

    for word in words:
        if current and _label(word.get("speaker")) != _label(current[0].get("speaker")):
            flush()
            current = []
        current.append(word)
    flush()
    return [segment for segment in segments if segment.text]


def _label(speaker: Any) -> str:
    if speaker is None or speaker == "":
        return f"{SPEAKER_PREFIX}UNKNOWN"
    return f"{SPEAKER_PREFIX}{speaker}"


def estimated_stt_usd(duration_seconds: float) -> float:
    return round(duration_seconds / 60 * STT_USD_PER_MINUTE, 4)


class GoogleSttV2Transcriber:
    """One BatchRecognize call per audio file; results parsed inline from GCS output."""

    def __init__(
        self,
        *,
        project: str,
        output_gcs_prefix: str,
        location: str = "global",
        model: str = "latest_long",
        language: str = "en-US",
        timeout_seconds: int = 1800,
    ) -> None:
        self._project = project
        self._location = location
        self._model = model
        self._language = language
        self._output_prefix = output_gcs_prefix
        self._timeout = timeout_seconds

    def transcribe(self, audio_uri: str) -> tuple[list[TranscriptSegment], bool]:
        try:
            return self._run(audio_uri, diarization=True), True
        except Exception as exc:  # diarization unsupported → honest fallback, logged
            logger.warning("diarized STT failed (%s); retrying without diarization", exc)
            return self._run(audio_uri, diarization=False), False

    def _run(self, audio_uri: str, *, diarization: bool) -> list[TranscriptSegment]:
        from google.cloud import speech_v2
        from google.cloud.speech_v2.types import cloud_speech

        client = speech_v2.SpeechClient()
        features = cloud_speech.RecognitionFeatures(
            enable_word_time_offsets=True,
            enable_automatic_punctuation=True,
        )
        if diarization:
            features.diarization_config = cloud_speech.SpeakerDiarizationConfig(
                min_speaker_count=2, max_speaker_count=6
            )
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=[self._language],
            model=self._model,
            features=features,
        )
        request = cloud_speech.BatchRecognizeRequest(
            recognizer=f"projects/{self._project}/locations/{self._location}/recognizers/_",
            config=config,
            files=[cloud_speech.BatchRecognizeFileMetadata(uri=audio_uri)],
            recognition_output_config=cloud_speech.RecognitionOutputConfig(
                inline_response_config=cloud_speech.InlineOutputConfig()
            ),
        )
        operation = client.batch_recognize(request=request)
        response = operation.result(timeout=self._timeout)  # type: ignore[no-untyped-call]
        words: list[dict[str, Any]] = []
        for file_result in response.results.values():
            for result in file_result.transcript.results:
                if not result.alternatives:
                    continue
                alternative = result.alternatives[0]
                for word in alternative.words:
                    words.append(
                        {
                            "word": word.word,
                            "start_ms": int(word.start_offset.total_seconds() * 1000),
                            "end_ms": int(word.end_offset.total_seconds() * 1000),
                            "speaker": word.speaker_label or None,
                            "confidence": word.confidence or alternative.confidence or None,
                        }
                    )
        return segments_from_batch_words(words)
