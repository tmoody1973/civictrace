"""Stable idempotency keys. Same source version + job type + agent version → same key, always."""

from __future__ import annotations

import hashlib

from app.schemas.source import SourceEvent

KEY_PREFIX = "sha256:"
SOURCE_JOB_TYPE = "PROCESS_SOURCE"
_SEPARATOR = "\n"


def build_job_key(event: SourceEvent, *, job_type: str, agent_version: str) -> str:
    """Hash the source version identity, not the observation (event id / time are excluded)."""
    material = _SEPARATOR.join(
        (
            event.source_id,
            event.external_id,
            event.content_hash or "",
            job_type,
            agent_version,
        )
    )
    return KEY_PREFIX + hashlib.sha256(material.encode("utf-8")).hexdigest()


class SourceJobKeys:
    """Adapter matching the workflow's IdempotencyService protocol."""

    def source_job_key(self, event: SourceEvent, *, workflow_version: str) -> str:
        return build_job_key(event, job_type=SOURCE_JOB_TYPE, agent_version=workflow_version)
