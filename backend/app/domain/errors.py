"""Typed domain exceptions. Pure: stdlib only."""

from __future__ import annotations


class CivicTraceError(Exception):
    """Base class for domain errors."""


class EvidenceValidationError(CivicTraceError):
    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons
