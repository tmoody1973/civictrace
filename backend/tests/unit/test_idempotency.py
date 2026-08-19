"""Same source version + same job + same agent version → same key. Change any input → new key."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.orchestration.idempotency import SourceJobKeys, build_job_key
from app.schemas.source import SourceEvent

GOLDEN_KEY = "sha256:4084a5a6ac80244f8b4e5b96be1251df9d0ffd94a17200a55493aa4b5800b37b"


def _event(**overrides: object) -> SourceEvent:
    base = {
        "source_event_id": "evt-1",
        "source_id": "milwaukee_legistar",
        "jurisdiction": "milwaukee_city",
        "artifact_id": "tid121-project-plan-2024",
        "external_id": "240382/attachment/223678",
        "canonical_url": "https://milwaukee.legistar1.com/milwaukee/attachments/x.pdf",
        "media_type": "application/pdf",
        "content_hash": "sha256:7097a1ba",
        "observed_at": datetime(2026, 8, 19, tzinfo=UTC),
    }
    return SourceEvent.model_validate({**base, **overrides})


def test_key_is_deterministic_and_matches_golden() -> None:
    key = build_job_key(_event(), job_type="PROCESS_SOURCE", agent_version="city-document.v1")
    assert key == build_job_key(
        _event(), job_type="PROCESS_SOURCE", agent_version="city-document.v1"
    )
    assert key == GOLDEN_KEY


def test_key_ignores_observation_time_and_event_id() -> None:
    later = _event(source_event_id="evt-2", observed_at=datetime(2027, 1, 1, tzinfo=UTC))
    assert build_job_key(_event(), job_type="P", agent_version="v1") == build_job_key(
        later, job_type="P", agent_version="v1"
    )


@pytest.mark.parametrize(
    "change",
    [
        {"source_id": "milwaukee_open_data"},
        {"external_id": "240382/attachment/999999"},
        {"content_hash": "sha256:different"},
    ],
)
def test_changing_any_source_input_changes_key(change: dict) -> None:
    base = build_job_key(_event(), job_type="P", agent_version="v1")
    assert build_job_key(_event(**change), job_type="P", agent_version="v1") != base


def test_changing_job_type_or_agent_version_changes_key() -> None:
    base = build_job_key(_event(), job_type="P", agent_version="v1")
    assert build_job_key(_event(), job_type="Q", agent_version="v1") != base
    assert build_job_key(_event(), job_type="P", agent_version="v2") != base


def test_source_job_keys_adapter_matches_workflow_protocol() -> None:
    keys = SourceJobKeys()
    assert keys.source_job_key(_event(), workflow_version="city-document.v1") == build_job_key(
        _event(), job_type="PROCESS_SOURCE", agent_version="city-document.v1"
    )


def test_same_bytes_at_a_new_url_is_the_same_job() -> None:
    # The City moving the PDF to a new link is not a new source version.
    moved = _event(canonical_url="https://milwaukee.legistar1.com/milwaukee/attachments/moved.pdf")
    assert build_job_key(_event(), job_type="P", agent_version="v1") == build_job_key(
        moved, job_type="P", agent_version="v1"
    )
