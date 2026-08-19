"""Evidence → case link → frozen bundle → Delta Investigator (fake) → checks → ledger."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.domain.enums import DeltaCategory, JobStatus, LedgerEventType
from app.services.corpus import load_corpus_manifest
from app.services.replay import ReplayOptions, build_workflow
from tests.conftest import ALLOWLIST_PATH, FIXTURE_DIR, MANIFEST_PATH, REPO_ROOT

NOW = datetime(2026, 8, 19, 17, 0, tzinfo=UTC)
PLAN, ANNUAL, AMEND, MISSING = (
    "tid121-project-plan-2024",
    "tid-annual-report-2024",
    "tid121-amendment-1-2026",
    "tid-annual-report-2025",
)


def _options(tmp_path: Path) -> ReplayOptions:
    return ReplayOptions(
        manifest_path=MANIFEST_PATH,
        allowlist_path=ALLOWLIST_PATH,
        extraction_path=FIXTURE_DIR / "fixture_extraction.json",
        fixture_root=REPO_ROOT,
        vault_dir=tmp_path / "vault",
    )


def _run(tmp_path: Path, artifact_ids: list[str]):
    manifest = load_corpus_manifest(MANIFEST_PATH)
    workflow, ledger = build_workflow(manifest, _options(tmp_path), clock=lambda: NOW)
    results = [
        asyncio.run(workflow.run(manifest.source_event(a), trace_id=f"t-{i}"))
        for i, a in enumerate(artifact_ids)
    ]
    return results, ledger


def _of(ledger, kind: LedgerEventType):  # noqa: ANN001, ANN202
    return [e for e in ledger.events() if e.event_type is kind]


def test_plan_alone_yields_no_delta_and_no_agent_call(tmp_path: Path) -> None:
    results, ledger = _run(tmp_path, [PLAN])
    assert results[0].status is JobStatus.SUCCEEDED
    assert _of(ledger, LedgerEventType.DELTA_PROPOSED) == []
    assert len(_of(ledger, LedgerEventType.NO_MATERIAL_DELTA)) == 1
    assert (
        _of(ledger, LedgerEventType.NO_MATERIAL_DELTA)[0].reason
        and "no later evidence" in _of(ledger, LedgerEventType.NO_MATERIAL_DELTA)[0].reason
    )


def test_full_corpus_yields_exactly_one_revised_delta(tmp_path: Path) -> None:
    results, ledger = _run(tmp_path, [PLAN, ANNUAL, AMEND, MISSING])
    assert [r.status for r in results] == [
        JobStatus.SUCCEEDED,
        JobStatus.SUCCEEDED,
        JobStatus.SUCCEEDED,
        JobStatus.NOT_PUBLISHED,
    ]
    proposed = _of(ledger, LedgerEventType.DELTA_PROPOSED)
    assert len(proposed) == 1
    delta = proposed[0].delta
    assert delta is not None and delta.category is DeltaCategory.REVISED
    assert delta.original_evidence_ids == ["ev-tid121-plan-capital-costs"]
    assert set(delta.later_evidence_ids) == {
        "ev-tid121-amend1-capital-costs",
        "ev-tid121-amend1-commercial-grant",
    }
    assert any("$700,000" in s for s in delta.what_is_established)
    assert any("$2,345,000" in s for s in delta.what_is_established)
    assert "2025 Annual Report" in (delta.next_evidence_needed or "")
    assert delta.requires_human_review is True
    # annual report → explicit NO_MATERIAL_DELTA, agent consulted
    no_material = _of(ledger, LedgerEventType.NO_MATERIAL_DELTA)
    assert {e.payload_ref for e in no_material} >= {ANNUAL}
    assert _of(ledger, LedgerEventType.DELTA_REJECTED) == []
    # Quality Reviewer (2.4) approves the fixture delta: staged, not human review
    assert _of(ledger, LedgerEventType.CASE_HUMAN_REVIEW) == []
    assert len(_of(ledger, LedgerEventType.DELTA_STAGED)) == 1
    assert results[2].staged_case_ids == ("case-tid121-bronzeville-arts-tech-hub",)


def test_rerun_adds_no_delta_events(tmp_path: Path) -> None:
    manifest = load_corpus_manifest(MANIFEST_PATH)
    workflow, ledger = build_workflow(manifest, _options(tmp_path), clock=lambda: NOW)
    for a in [PLAN, AMEND]:
        asyncio.run(workflow.run(manifest.source_event(a), trace_id="t"))
    before = len(ledger.events())
    again = asyncio.run(workflow.run(manifest.source_event(AMEND), trace_id="t2"))
    assert again.status is JobStatus.DUPLICATE_SUPPRESSED
    assert len(ledger.events()) == before


@pytest.mark.parametrize(
    ("label", "mutate"),
    [
        ("later side missing", lambda p: p.__setitem__("later_evidence_ids", [])),
        ("id not in bundle", lambda p: p.__setitem__("later_evidence_ids", ["ev-made-up"])),
        (
            "causal summary",
            lambda p: p.__setitem__(
                "neutral_summary", "Costs rose because the developer mismanaged funds."
            ),
        ),
        (
            "allegation word",
            lambda p: p.__setitem__("what_is_not_established", ["Whether this was fraud."]),
        ),
    ],
)
def test_tampered_delta_is_rejected_as_ledger_event(tmp_path: Path, label: str, mutate) -> None:  # noqa: ANN001
    import copy
    import json  # noqa: PLC0415

    payload = json.loads((FIXTURE_DIR / "fixture_delta.json").read_text())
    tampered = copy.deepcopy(payload)
    mutate(tampered["proposals"][AMEND])
    delta_path = tmp_path / "fixture_delta.json"
    delta_path.write_text(json.dumps(tampered))
    manifest = load_corpus_manifest(MANIFEST_PATH)
    options = ReplayOptions(
        manifest_path=MANIFEST_PATH,
        allowlist_path=ALLOWLIST_PATH,
        extraction_path=FIXTURE_DIR / "fixture_extraction.json",
        delta_path=delta_path,
        fixture_root=REPO_ROOT,
        vault_dir=tmp_path / "vault",
    )
    workflow, ledger = build_workflow(manifest, options, clock=lambda: NOW)
    for a in [PLAN, AMEND]:
        asyncio.run(workflow.run(manifest.source_event(a), trace_id="t"))
    rejected = _of(ledger, LedgerEventType.DELTA_REJECTED)
    assert len(rejected) == 1 and rejected[0].reason, label
    assert _of(ledger, LedgerEventType.DELTA_PROPOSED) == [], label
