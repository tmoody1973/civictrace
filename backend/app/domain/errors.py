"""Typed domain exceptions. Pure: stdlib only."""

from __future__ import annotations


class CivicTraceError(Exception):
    """Base class for domain errors."""


class EvidenceValidationError(CivicTraceError):
    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


class SourcePolicyError(CivicTraceError):
    """A source event names a domain, scheme, content type, or source_id that is not allowlisted."""


class ArtifactImmutabilityError(CivicTraceError):
    """Different bytes were offered for an artifact_id that is already stored."""


class FixtureIntegrityError(CivicTraceError):
    """A reviewed fixture file no longer matches the hash recorded in the manifest."""


class DuplicateJobError(CivicTraceError):
    """A job with this idempotency key is already running or already succeeded."""
