"""Deterministic validation gates. Agents propose; this code decides what may enter the ledger."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.enums import AnchorType, ArtifactAvailability
from app.domain.errors import EvidenceValidationError
from app.policies.privacy_policy import find_pii
from app.schemas.case import DecisionDelta
from app.schemas.evidence import DocumentExtraction, Evidence, EvidenceAnchor
from app.schemas.source import Artifact
from app.services.artifact_text import normalise_for_match


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


def validate_delta(delta: DecisionDelta) -> ValidationResult:
    reasons: list[str] = []
    if not delta.original_evidence_ids:
        reasons.append("delta has no original (Promise) evidence")
    if not delta.later_evidence_ids:
        reasons.append("delta has no later evidence")
    return ValidationResult(tuple(reasons))
