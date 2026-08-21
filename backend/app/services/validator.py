"""Deterministic validation gates. Agents propose; this code decides what may enter the ledger."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.enums import (
    AnchorType,
    ArtifactAvailability,
    DeltaResultType,
    EvidenceObjectType,
)
from app.domain.errors import EvidenceValidationError
from app.policies.language_policy import find_allegation_language, find_causal_language
from app.policies.privacy_policy import find_pii, find_restricted_scope
from app.schemas.case import CaseBundle, DecisionDelta, DecisionDeltaProposal
from app.schemas.evidence import (
    DocumentExtraction,
    Evidence,
    EvidenceAnchor,
    MediaEvidence,
    MediaExtraction,
)
from app.schemas.inquiry import InquiryProposal
from app.schemas.source import Artifact
from app.schemas.transcript import TranscriptArtifact
from app.services.artifact_text import normalise_for_match
from app.tools.transcript_tools import segments_overlapping


@dataclass(frozen=True)
class ValidationResult:
    reasons: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.reasons

    def raise_if_failed(self) -> None:
        if self.reasons:
            raise EvidenceValidationError(self.reasons)


def validate_extraction(
    extraction: DocumentExtraction,
    artifact: Artifact,
    page_texts: Sequence[str] | None = None,
) -> ValidationResult:
    """page_texts, when supplied, lets the gate verify quoted words exist on the anchored page."""
    reasons: list[str] = []
    if artifact.availability is not ArtifactAvailability.AVAILABLE:
        reasons.append(
            f"artifact {artifact.artifact_id} is {artifact.availability}; no evidence allowed"
        )
    if extraction.artifact_id != artifact.artifact_id:
        reasons.append(
            f"extraction targets {extraction.artifact_id}, artifact is {artifact.artifact_id}"
        )
    for item in extraction.evidence:
        reasons.extend(_evidence_reasons(item, artifact, page_texts))
    return ValidationResult(tuple(reasons))


def _evidence_reasons(
    item: Evidence, artifact: Artifact, page_texts: Sequence[str] | None
) -> list[str]:
    reasons: list[str] = []
    if not item.anchors:
        reasons.append(f"{item.evidence_id}: no anchor")
    for kind in find_pii(item.verbatim_excerpt + " " + item.neutral_statement):
        reasons.append(f"{item.evidence_id}: {kind} pattern in evidence text")
    for term in find_allegation_language(item.neutral_statement):
        reasons.append(f"{item.evidence_id}: allegation language in neutral_statement ({term!r})")
    if item.artifact_id != artifact.artifact_id:
        reasons.append(f"{item.evidence_id}: evidence names unknown artifact {item.artifact_id}")
    for anchor in item.anchors:
        reasons.extend(_anchor_reasons(item.evidence_id, anchor, artifact))
        reasons.extend(_quote_reasons(item, anchor, page_texts))
    return reasons


def _quote_reasons(
    item: Evidence, anchor: EvidenceAnchor, page_texts: Sequence[str] | None
) -> list[str]:
    if page_texts is None or anchor.anchor_type is not AnchorType.PAGE:
        return []
    page = _parse_page(anchor.anchor_value)
    if page is None or not 1 <= page <= len(page_texts):
        return []  # page-range problems are reported by _anchor_reasons
    if normalise_for_match(item.verbatim_excerpt) not in normalise_for_match(page_texts[page - 1]):
        return [f"{item.evidence_id}: quoted words not found on page {page}"]
    return []


def _anchor_reasons(evidence_id: str, anchor: EvidenceAnchor, artifact: Artifact) -> list[str]:
    if anchor.artifact_id != artifact.artifact_id:
        return [f"{evidence_id}: anchor names unknown artifact {anchor.artifact_id}"]
    if anchor.anchor_type is AnchorType.PAGE and artifact.page_count is not None:
        page = _parse_page(anchor.anchor_value)
        if page is None or page < 1 or page > artifact.page_count:
            return [f"{evidence_id}: page {anchor.anchor_value} outside 1..{artifact.page_count}"]
    return []


def _parse_page(value: str) -> int | None:
    return int(value) if value.isdigit() else None


# Words that mark a committee/council action in a transcript span. A DECISION or VOTE
# evidence object without one of these in its anchored span is discussion, not an action.
ACTION_SPAN_TERMS = (
    "motion",
    "moved",
    "move approval",
    "second",
    "aye",
    "vote",
    "passes",
    "passed",
    "carried",
    "recommend",
    "adopted",
    "approval",
)


def validate_media_extraction(
    extraction: MediaExtraction, artifact: Artifact, transcript: TranscriptArtifact
) -> ValidationResult:
    """Deterministic gate for meeting evidence: exact timestamp anchors, quotes that exist in
    the transcript, and diarization labels that stay labels."""
    reasons: list[str] = []
    if artifact.availability is not ArtifactAvailability.AVAILABLE:
        reasons.append(
            f"artifact {artifact.artifact_id} is {artifact.availability}; no evidence allowed"
        )
    if extraction.artifact_id != artifact.artifact_id:
        reasons.append(
            f"extraction targets {extraction.artifact_id}, artifact is {artifact.artifact_id}"
        )
    if extraction.transcript_id != transcript.transcript_id:
        reasons.append(
            f"extraction cites transcript {extraction.transcript_id}, "
            f"supplied transcript is {transcript.transcript_id}"
        )
    for item in extraction.evidence:
        reasons.extend(_media_evidence_reasons(item, artifact, transcript))
    return ValidationResult(tuple(reasons))


def _media_evidence_reasons(
    item: MediaEvidence, artifact: Artifact, transcript: TranscriptArtifact
) -> list[str]:
    reasons: list[str] = []
    if not item.anchors:
        reasons.append(f"{item.evidence_id}: no anchor")
    for kind in find_pii(item.verbatim_excerpt + " " + item.neutral_statement):
        reasons.append(f"{item.evidence_id}: {kind} pattern in evidence text")
    for term in find_allegation_language(item.neutral_statement):
        reasons.append(f"{item.evidence_id}: allegation language in neutral_statement ({term!r})")
    if item.artifact_id != artifact.artifact_id:
        reasons.append(f"{item.evidence_id}: evidence names unknown artifact {item.artifact_id}")
    spans = []
    for anchor in item.anchors:
        if anchor.artifact_id != artifact.artifact_id:
            reasons.append(
                f"{item.evidence_id}: anchor names unknown artifact {anchor.artifact_id}"
            )
            continue
        span_reasons, span = _transcript_anchor_reasons(item.evidence_id, anchor, transcript)
        reasons.extend(span_reasons)
        if span is not None:
            spans.append(span)
    if spans:
        span_text = normalise_for_match(
            " ".join(
                segment.text
                for start_ms, end_ms in spans
                for segment in segments_overlapping(transcript, start_ms, end_ms)
            )
        )
        span_labels = {
            segment.speaker_label
            for start_ms, end_ms in spans
            for segment in segments_overlapping(transcript, start_ms, end_ms)
        }
        if normalise_for_match(item.verbatim_excerpt) not in span_text:
            reasons.append(f"{item.evidence_id}: quoted words not found in the anchored span")
        if item.speaker_label is not None and item.speaker_label not in span_labels:
            reasons.append(
                f"{item.evidence_id}: speaker_label {item.speaker_label!r} is not a "
                "diarization label of the anchored span (a name is not a label)"
            )
        if (
            item.object_type in (EvidenceObjectType.DECISION, EvidenceObjectType.VOTE)
            and not any(term in span_text for term in ACTION_SPAN_TERMS)
        ):
            reasons.append(
                f"{item.evidence_id}: {item.object_type} anchored to a span with no "
                "motion/vote language; meeting discussion is not an institutional action"
            )
    return reasons


def _transcript_anchor_reasons(
    evidence_id: str, anchor: EvidenceAnchor, transcript: TranscriptArtifact
) -> tuple[list[str], tuple[int, int] | None]:
    """Anchors must be `start_ms-end_ms` inside the transcribed segment. Returns the span."""
    if anchor.anchor_type is not AnchorType.TRANSCRIPT_TIME:
        return [f"{evidence_id}: media evidence requires a transcript_time anchor"], None
    parts = anchor.anchor_value.split("-")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return [
            f"{evidence_id}: anchor {anchor.anchor_value!r} is not '<start_ms>-<end_ms>'"
        ], None
    start_ms, end_ms = int(parts[0]), int(parts[1])
    duration_ms = transcript.duration_seconds() * 1000
    if start_ms >= end_ms or end_ms > duration_ms:
        return [
            f"{evidence_id}: anchor {anchor.anchor_value!r} outside 0..{duration_ms} ms"
        ], None
    return [], (start_ms, end_ms)


def validate_delta(
    delta: DecisionDelta | DecisionDeltaProposal, bundle: CaseBundle | None = None
) -> ValidationResult:
    """A delta enters the ledger only if both sides are anchored and the words are neutral."""
    reasons: list[str] = []
    reasons.extend(_delta_side_reasons(delta))
    if bundle is not None:
        reasons.extend(_delta_bundle_reasons(delta, bundle))
    reasons.extend(_delta_language_reasons(delta))
    if not delta.requires_human_review:
        reasons.append("requires_human_review must be true; no delta is final without a person")
    return ValidationResult(tuple(reasons))


def _delta_side_reasons(delta: DecisionDelta | DecisionDeltaProposal) -> list[str]:
    is_material = (
        not isinstance(delta, DecisionDeltaProposal)
        or delta.result_type is DeltaResultType.DECISION_DELTA
    )
    if not is_material:
        return []
    reasons: list[str] = []
    if not delta.original_evidence_ids:
        reasons.append("delta has no original (Promise) evidence")
    if not delta.later_evidence_ids:
        reasons.append("delta has no later evidence")
    return reasons


def _delta_bundle_reasons(delta: DecisionDelta, bundle: CaseBundle) -> list[str]:
    original, later = bundle.original_ids(), bundle.later_ids()
    reasons: list[str] = []
    for evidence_id in delta.original_evidence_ids:
        if evidence_id in later:
            reasons.append(f"{evidence_id}: wrong side (later evidence listed as original)")
        elif evidence_id not in original:
            reasons.append(f"{evidence_id}: not in bundle")
    for evidence_id in delta.later_evidence_ids:
        if evidence_id in original:
            reasons.append(f"{evidence_id}: wrong side (original evidence listed as later)")
        elif evidence_id not in later:
            reasons.append(f"{evidence_id}: not in bundle")
    return reasons


def validate_inquiry(proposal: InquiryProposal, bundle: CaseBundle) -> ValidationResult:
    """An inquiry enters the ledger only if it is narrow, neutral, and cites bundle evidence.

    excluded_requests is deliberately NOT scanned for scope words: it is where the
    planner promises what it will not ask ("No student-level information.").
    """
    reasons: list[str] = []
    if not proposal.proposed_question.strip():
        reasons.append("proposed_question is empty")
    if proposal.approval_required is not True:
        reasons.append("approval_required must be true; no inquiry moves without a person")
    reasons.extend(_inquiry_language_reasons(proposal))
    reasons.extend(_inquiry_evidence_reasons(proposal, bundle))
    return ValidationResult(tuple(reasons))


def _inquiry_language_reasons(proposal: InquiryProposal) -> list[str]:
    texts = (
        ("proposed_question", proposal.proposed_question),
        ("scope_rationale", proposal.scope_rationale),
        ("target_record_or_source", proposal.target_record_or_source),
        *(("limitations", text) for text in proposal.limitations),
    )
    reasons: list[str] = []
    for field_name, text in texts:
        for term in find_allegation_language(text):
            reasons.append(f"allegation language in {field_name} ({term!r})")
        for term in find_causal_language(text):
            reasons.append(f"causal language in {field_name} ({term!r})")
        for term in find_restricted_scope(text):
            reasons.append(f"student/personnel scope in {field_name} ({term!r})")
    return reasons


def _inquiry_evidence_reasons(proposal: InquiryProposal, bundle: CaseBundle) -> list[str]:
    if not proposal.supporting_evidence_ids:
        return ["inquiry cites no supporting evidence"]
    known = bundle.original_ids() | bundle.later_ids()
    return [
        f"{evidence_id}: not in bundle"
        for evidence_id in proposal.supporting_evidence_ids
        if evidence_id not in known
    ]


def _delta_language_reasons(delta: DecisionDelta) -> list[str]:
    reasons: list[str] = []
    texts = [delta.neutral_summary, *delta.what_is_established, *delta.what_is_not_established]
    for text in texts:
        for term in find_allegation_language(text):
            reasons.append(f"allegation language in delta text ({term!r})")
    for term in find_causal_language(delta.neutral_summary):
        reasons.append(f"causal language in neutral_summary ({term!r})")
    return reasons
