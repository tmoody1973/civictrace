"""In-memory job repo and append-only ledger."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from app.domain.enums import JobStatus, LedgerEventType
from app.domain.errors import DuplicateJobError
from app.orchestration.workflow import WorkflowContext
from app.repositories.cases import AppendOutcome, InMemoryLedger, ledger_event_id
from app.repositories.jobs import InMemoryJobRepository
from app.schemas.case import LedgerEvent

CTX = WorkflowContext(trace_id="trace-1", job_key="job-1")
FIXED_NOW = datetime(2026, 8, 19, 14, 0, tzinfo=UTC)


def _run(coro):  # noqa: ANN001, ANN202 - tiny async helper for tests
    return asyncio.run(coro)


def test_job_lifecycle_and_duplicate_start() -> None:
    jobs = InMemoryJobRepository()
    assert _run(jobs.exists_terminal("job-1")) is False
    _run(jobs.start("job-1", context=CTX))
    with pytest.raises(DuplicateJobError):
        _run(jobs.start("job-1", context=CTX))
    _run(jobs.succeed("job-1", context=CTX))
    assert _run(jobs.exists_terminal("job-1")) is True
    with pytest.raises(DuplicateJobError):
        _run(jobs.start("job-1", context=CTX))


def test_failed_job_may_be_retried() -> None:
    jobs = InMemoryJobRepository()
    _run(jobs.start("job-1", context=CTX))
    _run(jobs.fail("job-1", error_code="FixtureIntegrityError", context=CTX))
    assert _run(jobs.exists_terminal("job-1")) is False
    assert jobs.status("job-1") is JobStatus.FAILED
    _run(jobs.start("job-1", context=CTX))  # retry allowed


def _event(payload_ref: str = "ev-1") -> LedgerEvent:
    return LedgerEvent(
        event_id=ledger_event_id("job-1", LedgerEventType.EVIDENCE_ACCEPTED, payload_ref),
        case_id="case-1",
        job_key="job-1",
        event_type=LedgerEventType.EVIDENCE_ACCEPTED,
        payload_ref=payload_ref,
        occurred_at=FIXED_NOW,
        actor="system",
    )


def test_ledger_appends_once_per_event_id() -> None:
    ledger = InMemoryLedger(
        case_id="case-1", clock=lambda: FIXED_NOW, original_artifact_ids=frozenset()
    )
    assert ledger.append(_event()) is AppendOutcome.APPENDED
    assert ledger.append(_event()) is AppendOutcome.DUPLICATE_SUPPRESSED
    assert len(ledger.events()) == 1


def test_ledger_keeps_distinct_payloads_for_same_job_and_type() -> None:
    ledger = InMemoryLedger(
        case_id="case-1", clock=lambda: FIXED_NOW, original_artifact_ids=frozenset()
    )
    ledger.append(_event("ev-1"))
    ledger.append(_event("ev-2"))
    assert [event.payload_ref for event in ledger.events()] == ["ev-1", "ev-2"]


def test_ledger_has_no_update_or_delete() -> None:
    forbidden = {
        name
        for name in dir(InMemoryLedger)
        if name.startswith(("update", "delete", "remove", "pop", "clear"))
    }
    assert not forbidden, forbidden


def test_events_returns_a_copy() -> None:
    ledger = InMemoryLedger(
        case_id="case-1", clock=lambda: FIXED_NOW, original_artifact_ids=frozenset()
    )
    ledger.append(_event())
    ledger.events().clear()
    assert len(ledger.events()) == 1
