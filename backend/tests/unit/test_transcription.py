"""Transcript segment grouping: pure parsing, no network (Slice 6.2, MOO-716)."""

from __future__ import annotations

from app.services.transcription import estimated_stt_usd, segments_from_batch_words


def _word(text: str, start: int, end: int, speaker: str | None, conf: float | None = 0.9) -> dict:
    return {"word": text, "start_ms": start, "end_ms": end, "speaker": speaker, "confidence": conf}


def test_words_group_into_segments_split_on_speaker_change() -> None:
    segments = segments_from_batch_words(
        [
            _word("Good", 0, 300, "1"),
            _word("morning.", 320, 700, "1"),
            _word("Thank", 900, 1100, "2"),
            _word("you.", 1120, 1400, "2"),
        ]
    )
    assert [(s.speaker_label, s.text) for s in segments] == [
        ("SPEAKER_1", "Good morning."),
        ("SPEAKER_2", "Thank you."),
    ]
    assert (segments[0].start_ms, segments[0].end_ms) == (0, 700)


def test_missing_speaker_becomes_unknown_label_and_is_kept() -> None:
    segments = segments_from_batch_words([_word("inaudible", 0, 500, None, None)])
    assert segments[0].speaker_label == "SPEAKER_UNKNOWN"
    assert segments[0].confidence is None  # low/no confidence preserved, never invented


def test_segment_confidence_is_the_minimum_word_confidence() -> None:
    segments = segments_from_batch_words(
        [_word("clear", 0, 300, "1", 0.95), _word("mumbled", 320, 600, "1", 0.41)]
    )
    assert segments[0].confidence == 0.41


def test_stt_cost_estimate() -> None:
    assert estimated_stt_usd(703) == round(703 / 60 * 0.016, 4)
