"""Staged delta → Inquiry Planner (fake) → validate_inquiry → INQUIRY_STAGED or INQUIRY_REJECTED."""

from __future__ import annotations

import asyncio
import copy
import json
from datetime import UTC, datetime
from pathlib import Path

from app.domain.enums import LedgerEventType
from app.services.corpus import load_corpus_manifest
from app.services.replay import ReplayOptions, build_workflow
from app.services.trace import build_trace
from tests.conftest import ALLOWLIST_PATH, FIXTURE_DIR, MANIFEST_PATH, REPO_ROOT

NOW = datetime(2026, 8, 19, 18, 0, tzinfo=UTC)
PLAN, AMEND = "tid121-project-plan-2024", "tid121-amendment-1-2026"
CASE_ID = "case-tid121-bronzeville-arts-tech-hub"


def _options(tmp_path: Path, inquiry_path: Path | None = None) -> ReplayOptions:
    return ReplayOptions(
        manifest_path=MANIFEST_PATH,
        allowlist_path=ALLOWLIST_PATH,
        extraction_path=FIXTURE_DIR / "fixture_extraction.json",
        fixture_root=REPO_ROOT,
        vault_dir=tmp_path / "vault",
        inquiry_path=inquiry_path,
    )


def _run(tmp_path: Path, inquiry_path: Path | None = None):
    manifest = load_corpus_manifest(MANIFEST_PATH)
    workflow, ledger, _ = build_workflow(
        manifest, _options(tmp_path, inquiry_path), clock=lambda: NOW
    )
    for index, artifact_id in enumerate([PLAN, AMEND]):
        asyncio.run(workflow.run(manifest.source_event(artifact_id), trace_id=f"t-{index}"))
    return workflow, ledger


def _of(ledger, kind: LedgerEventType):  # noqa: ANN001, ANN202
    return [e for e in ledger.events() if e.event_type is kind]


def test_staged_delta_stages_exactly_one_inquiry(tmp_path: Path) -> None:
    _, ledger = _run(tmp_path)
    staged = _of(ledger, LedgerEventType.INQUIRY_STAGED)
    assert len(staged) == 1
    inquiry = staged[0].inquiry
    assert inquiry is not None
    assert "2025 Annual Report" in inquiry.proposed_question
    assert inquiry.approval_required is True
    assert _of(ledger, LedgerEventType.INQUIRY_REJECTED) == []
    kinds = [e.event_type for e in ledger.events()]
    assert kinds.index(LedgerEventType.DELTA_STAGED) < kinds.index(
        LedgerEventType.INQUIRY_STAGED
    )


def test_accusatory_fixture_is_rejected_with_reason(tmp_path: Path) -> None:
    payload = json.loads((FIXTURE_DIR / "fixture_inquiry.json").read_text())
    tampered = copy.deepcopy(payload)
    tampered["proposals"][CASE_ID]["proposed_question"] = (
        "Why is the City covering up its corruption in the missing 2025 report?"
    )
    inquiry_path = tmp_path / "fixture_inquiry.json"
    inquiry_path.write_text(json.dumps(tampered))
    _, ledger = _run(tmp_path, inquiry_path)
    assert _of(ledger, LedgerEventType.INQUIRY_STAGED) == []
    rejected = _of(ledger, LedgerEventType.INQUIRY_REJECTED)
    assert len(rejected) == 1
    assert rejected[0].reason is not None and "corruption" in rejected[0].reason


def test_rerun_adds_no_inquiry_events(tmp_path: Path) -> None:
    workflow, ledger = _run(tmp_path)
    manifest = load_corpus_manifest(MANIFEST_PATH)
    before = len(ledger.events())
    asyncio.run(workflow.run(manifest.source_event(AMEND), trace_id="t-again"))
    assert len(ledger.events()) == before
    assert len(_of(ledger, LedgerEventType.INQUIRY_STAGED)) == 1


def test_trace_exposes_inquiry_rows(tmp_path: Path) -> None:
    _, ledger = _run(tmp_path)
    trace = build_trace(CASE_ID, ledger.events())
    rows = [e for e in trace.events if e.event_type is LedgerEventType.INQUIRY_STAGED]
    assert len(rows) == 1
    row = rows[0]
    assert row.proposed_question is not None and "2025 Annual Report" in row.proposed_question
    assert row.inquiry_type is not None
    assert row.supporting_evidence_ids
