"""MOO-717: transcript-span tool, media validation gates, and ledger conversion.

The failure modes we refuse to ship: an unanchored meeting claim, a quote that is not
in the transcript, a diarization label upgraded to a person's name, and committee
discussion upgraded to an institutional action.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import (
    AnchorType,
    ArtifactAvailability,
    EvidenceObjectType,
    EvidenceStatus,
)
from app.schemas.evidence import EvidenceAnchor, MediaEvidence, MediaExtraction
from app.schemas.source import Artifact
from app.schemas.transcript import TranscriptArtifact, TranscriptSegment
from app.services.validator import validate_media_extraction
from app.tools.transcript_tools import TranscriptSpanReader

ARTIFACT_ID = "znd-committee-2026-07-28"
TRANSCRIPT_ID = "tr-znd-2026-07-28-tid121"


def _transcript() -> TranscriptArtifact:
    return TranscriptArtifact(
        transcript_id=TRANSCRIPT_ID,
        source_artifact_id=ARTIFACT_ID,
        segment_start_seconds=5287,
        segment_end_seconds=5990,
        audio_uri="gs://vault/segment.flac",
        audio_hash="sha256:abc",
        stt_provider="google-speech-v2",
        stt_model="chirp_3",
        diarization=True,
        created_at=datetime(2026, 8, 21, tzinfo=UTC),
        segments=[
            TranscriptSegment(
                start_ms=0,
                end_ms=10_000,
                speaker_label="SPEAKER_0",
                text="approving amendment number one to the project plan",
            ),
            TranscriptSegment(
                start_ms=10_000,
                end_ms=60_000,
                speaker_label="SPEAKER_1",
                text="Amendment one to this TID will fund the commercial component.",
            ),
            TranscriptSegment(
                start_ms=690_000,
                end_ms=700_000,
                speaker_label="SPEAKER_0",
                text="moves to recommend adoption. Hearing no objections, so ordered.",
            ),
        ],
    )


def _artifact() -> Artifact:
    return Artifact(
        artifact_id=ARTIFACT_ID,
        source_id="milwaukee_legistar",
        canonical_url="https://milwaukee.granicus.com/MediaPlayer.php?clip_id=5262",
        external_id="event/13443/media/5262",
        title="ZND Committee meeting",
        media_type="video/mp4",
        content_hash="sha256:media",
        byte_length=3_094_814_441,
        page_count=None,
        storage_uri="gs://vault/znd-committee-2026-07-28.mp4",
        retrieved_at=datetime(2026, 8, 21, tzinfo=UTC),
        availability=ArtifactAvailability.AVAILABLE,
    )


def _evidence(**overrides: object) -> MediaEvidence:
    values: dict = {
        "evidence_id": "ev-1",
        "artifact_id": ARTIFACT_ID,
        "object_type": EvidenceObjectType.CLAIM,
        "verbatim_excerpt": "Amendment one to this TID will fund the commercial component.",
        "neutral_statement": "A presenter stated the amendment will fund the commercial component.",
        "anchors": [
            EvidenceAnchor(
                artifact_id=ARTIFACT_ID,
                anchor_type=AnchorType.TRANSCRIPT_TIME,
                anchor_value="10000-60000",
            )
        ],
        "status": EvidenceStatus.SUPPORTED,
        "speaker_label": "SPEAKER_1",
    }
    values.update(overrides)
    return MediaEvidence.model_validate(values)


def _extraction(*evidence: MediaEvidence) -> MediaExtraction:
    return MediaExtraction(
        artifact_id=ARTIFACT_ID,
        transcript_id=TRANSCRIPT_ID,
        agent_name="civictrace-media_evidence",
        agent_version="test",
        evidence=list(evidence),
    )


class TestTranscriptSpanReader:
    def test_reads_overlapping_segments_with_labels_and_bounds(self) -> None:
        reader = TranscriptSpanReader(artifact_id=ARTIFACT_ID, transcript=_transcript())
        text = reader.read_transcript_span(ARTIFACT_ID, 0, 60_000)
        assert "[10000-60000 ms] SPEAKER_1:" in text
        assert "commercial component" in text

    def test_refuses_other_artifact(self) -> None:
        reader = TranscriptSpanReader(artifact_id=ARTIFACT_ID, transcript=_transcript())
        assert reader.read_transcript_span("other", 0, 1_000).startswith("REFUSED")

    def test_refuses_oversized_span(self) -> None:
        reader = TranscriptSpanReader(artifact_id=ARTIFACT_ID, transcript=_transcript())
        assert reader.read_transcript_span(ARTIFACT_ID, 0, 400_000).startswith("REFUSED")

    def test_refuses_span_past_the_end(self) -> None:
        reader = TranscriptSpanReader(artifact_id=ARTIFACT_ID, transcript=_transcript())
        assert reader.read_transcript_span(ARTIFACT_ID, 800_000, 810_000).startswith("REFUSED")


class TestMediaValidation:
    def test_valid_extraction_passes(self) -> None:
        result = validate_media_extraction(_extraction(_evidence()), _artifact(), _transcript())
        assert result.ok, result.reasons

    def test_missing_anchor_fails(self) -> None:
        result = validate_media_extraction(
            _extraction(_evidence(anchors=[])), _artifact(), _transcript()
        )
        assert any("no anchor" in reason for reason in result.reasons)

    def test_page_anchor_fails_for_media(self) -> None:
        anchor = EvidenceAnchor(
            artifact_id=ARTIFACT_ID, anchor_type=AnchorType.PAGE, anchor_value="3"
        )
        result = validate_media_extraction(
            _extraction(_evidence(anchors=[anchor])), _artifact(), _transcript()
        )
        assert any("transcript_time" in reason for reason in result.reasons)

    def test_anchor_outside_segment_fails(self) -> None:
        anchor = EvidenceAnchor(
            artifact_id=ARTIFACT_ID,
            anchor_type=AnchorType.TRANSCRIPT_TIME,
            anchor_value="10000-99999999",
        )
        result = validate_media_extraction(
            _extraction(_evidence(anchors=[anchor])), _artifact(), _transcript()
        )
        assert any("outside" in reason for reason in result.reasons)

    def test_quote_not_in_span_fails(self) -> None:
        result = validate_media_extraction(
            _extraction(_evidence(verbatim_excerpt="words never spoken in the meeting")),
            _artifact(),
            _transcript(),
        )
        assert any("quoted words not found" in reason for reason in result.reasons)

    def test_speaker_name_instead_of_label_fails(self) -> None:
        result = validate_media_extraction(
            _extraction(_evidence(speaker_label="Lori Lutzka")), _artifact(), _transcript()
        )
        assert any("not a label" in reason for reason in result.reasons)

    def test_label_from_another_span_fails(self) -> None:
        result = validate_media_extraction(
            _extraction(_evidence(speaker_label="SPEAKER_0")), _artifact(), _transcript()
        )
        assert not validate_media_extraction(
            _extraction(_evidence(speaker_label="SPEAKER_1")), _artifact(), _transcript()
        ).reasons
        assert any("not a" in reason for reason in result.reasons)

    def test_discussion_cannot_become_a_decision(self) -> None:
        result = validate_media_extraction(
            _extraction(_evidence(object_type=EvidenceObjectType.DECISION)),
            _artifact(),
            _transcript(),
        )
        assert any("not an institutional action" in reason for reason in result.reasons)

    def test_decision_with_motion_language_passes(self) -> None:
        item = _evidence(
            object_type=EvidenceObjectType.DECISION,
            verbatim_excerpt="moves to recommend adoption. Hearing no objections, so ordered.",
            neutral_statement=(
                "The chair stated a motion to recommend adoption was ordered without objection."
            ),
            anchors=[
                EvidenceAnchor(
                    artifact_id=ARTIFACT_ID,
                    anchor_type=AnchorType.TRANSCRIPT_TIME,
                    anchor_value="690000-700000",
                )
            ],
            speaker_label="SPEAKER_0",
        )
        result = validate_media_extraction(_extraction(item), _artifact(), _transcript())
        assert result.ok, result.reasons

    def test_allegation_language_fails(self) -> None:
        result = validate_media_extraction(
            _extraction(
                _evidence(neutral_statement="The developer committed fraud at the hearing.")
            ),
            _artifact(),
            _transcript(),
        )
        assert any("allegation language" in reason for reason in result.reasons)

    def test_wrong_transcript_id_fails(self) -> None:
        extraction = _extraction(_evidence()).model_copy(update={"transcript_id": "tr-other"})
        result = validate_media_extraction(extraction, _artifact(), _transcript())
        assert any("supplied transcript" in reason for reason in result.reasons)


class TestLedgerConversion:
    def test_speaker_label_becomes_a_limitation_and_shape_stays_evidence(self) -> None:
        converted = _extraction(_evidence()).to_document_extraction()
        item = converted.evidence[0]
        assert type(item).__name__ == "Evidence"
        assert any("diarization label" in note for note in item.limitations)
        assert item.anchors[0].anchor_type is AnchorType.TRANSCRIPT_TIME

    def test_conversion_without_label_adds_nothing(self) -> None:
        converted = _extraction(_evidence(speaker_label=None)).to_document_extraction()
        assert converted.evidence[0].limitations == []


def test_media_route_selected_for_meeting_video() -> None:
    from app.orchestration.routes import CityRouteRegistry

    registry = CityRouteRegistry()
    assert registry.requires_media_extraction(_artifact())
    assert not registry.requires_document_extraction(_artifact())
