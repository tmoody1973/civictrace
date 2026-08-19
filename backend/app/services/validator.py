"""Deterministic validation gates. Agents propose; this code decides what may enter the ledger."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import AnchorType, ArtifactAvailability
from app.domain.errors import EvidenceValidationError
from app.schemas.case import DecisionDelta
from app.schemas.evidence import DocumentExtraction, Evidence, EvidenceAnchor
from app.schemas.source import Artifact


@dataclass(frozen=True)
class ValidationResult:
    reasons: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.reasons

    def raise_if_failed(self) -> None:
        if self.reasons:
            raise EvidenceValidationError(self.reasons)


def validate_extraction(extraction: DocumentExtraction, artifact: Artifact) -> ValidationResult:
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
        reasons.extend(_evidence_reasons(item, artifact))
    return ValidationResult(tuple(reasons))


def _evidence_reasons(item: Evidence, artifact: Artifact) -> list[str]:
    reasons: list[str] = []
    if not item.anchors:
        reasons.append(f"{item.evidence_id}: no anchor")
    if item.artifact_id != artifact.artifact_id:
        reasons.append(f"{item.evidence_id}: evidence names unknown artifact {item.artifact_id}")
    for anchor in item.anchors:
        reasons.extend(_anchor_reasons(item.evidence_id, anchor, artifact))
    return reasons


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
