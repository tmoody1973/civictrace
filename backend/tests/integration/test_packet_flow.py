"""Staged inquiry + valid token → one DRAFT packet. Anything else → refusal, no file."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.enums import ApprovalActionType, LedgerEventType
from app.services.approval import ApprovalService
from app.services.corpus import load_corpus_manifest
from app.services.packet import (
    find_staged_delta,
    find_staged_inquiry,
    inquiry_artifact_hash,
    render_inquiry_packet,
)
from app.services.packet_store import LocalPacketWriter
from app.services.replay import ReplayOptions, build_workflow
from tests.conftest import ALLOWLIST_PATH, FIXTURE_DIR, MANIFEST_PATH, REPO_ROOT

NOW = datetime(2026, 8, 19, 18, 0, tzinfo=UTC)
PLAN, AMEND = "tid121-project-plan-2024", "tid121-amendment-1-2026"
CASE_ID = "case-tid121-bronzeville-arts-tech-hub"
REVIEWER = "Tarik Moody"
GOLDEN_PATH = FIXTURE_DIR / "golden_inquiry_packet.md"


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture()
def staged(tmp_path: Path):
    """Replay the corpus once: (ledger, bundle, delta, inquiry, clock)."""
    manifest = load_corpus_manifest(MANIFEST_PATH)
    clock = MutableClock(NOW)
    options = ReplayOptions(
        manifest_path=MANIFEST_PATH,
        allowlist_path=ALLOWLIST_PATH,
        extraction_path=FIXTURE_DIR / "fixture_extraction.json",
        fixture_root=REPO_ROOT,
        vault_dir=tmp_path / "vault",
    )
    workflow, ledger, _ = build_workflow(manifest, options, clock=clock)
    for index, entry in enumerate(manifest.artifacts):
        asyncio.run(
            workflow.run(manifest.source_event(entry.artifact_id), trace_id=f"t-{index}")
        )
    events = ledger.events()
    delta = find_staged_delta(events)
    inquiry = find_staged_inquiry(events)
    bundle = ledger.build_case_bundle(trigger_artifact_id="", new_evidence_ids=[])
    return ledger, bundle, delta, inquiry, clock


def _render(staged, tmp_path: Path, *, token, approval, inquiry=None):  # noqa: ANN001, ANN202
    ledger, bundle, delta, staged_inquiry, _ = staged
    return render_inquiry_packet(
        bundle=bundle,
        delta=delta,
        inquiry=inquiry if inquiry is not None else staged_inquiry,
        events=ledger.events(),
        token=token,
        approval=approval,
        ledger=ledger,
        writer=LocalPacketWriter(tmp_path / "packets"),
    )


def _of(ledger, kind: LedgerEventType):  # noqa: ANN001, ANN202
    return [e for e in ledger.events() if e.event_type is kind]


def _issue(staged, clock):  # noqa: ANN001, ANN202
    ledger, _, _, inquiry, _ = staged
    approval = ApprovalService(clock=clock, ledger=ledger)
    token = approval.issue(
        case_id=CASE_ID,
        artifact_hash=inquiry_artifact_hash(inquiry),
        action_type=ApprovalActionType.RENDER_INQUIRY_PACKET,
        reviewer_name=REVIEWER,
    )
    return approval, token


def test_valid_token_renders_draft_packet(staged, tmp_path: Path) -> None:
    ledger, _, _, _, clock = staged
    approval, token = _issue(staged, clock)
    result = _render(staged, tmp_path, token=token, approval=approval)
    assert result.ok, result.reason
    assert result.packet_path is not None and Path(result.packet_path).exists()
    text = Path(result.packet_path).read_text()
    assert text.startswith("# DRAFT")
    assert "not sent; no external action taken" in text
    assert "2025 Annual Report of Tax Incremental Districts" in text
    assert "$700,000" in text and "$2,345,000" in text
    assert REVIEWER in text and token.token_id in text
    rendered = _of(ledger, LedgerEventType.PACKET_RENDERED)
    assert len(rendered) == 1
    assert rendered[0].payload_ref == result.packet_hash
    assert rendered[0].packet_path == result.packet_path


def test_no_token_refused_and_no_file(staged, tmp_path: Path) -> None:
    ledger, _, _, _, clock = staged
    approval = ApprovalService(clock=clock, ledger=ledger)
    result = _render(staged, tmp_path, token=None, approval=approval)
    assert not result.ok and result.reason == "approval token missing"
    assert not (tmp_path / "packets").exists() or not list((tmp_path / "packets").iterdir())
    refused = _of(ledger, LedgerEventType.APPROVAL_REFUSED)
    assert len(refused) == 1 and refused[0].reason == "approval token missing"
    assert _of(ledger, LedgerEventType.PACKET_RENDERED) == []


def test_edited_inquiry_invalidates_token(staged, tmp_path: Path) -> None:
    ledger, _, _, inquiry, clock = staged
    approval, token = _issue(staged, clock)
    edited = inquiry.model_copy(
        update={"proposed_question": inquiry.proposed_question + " And one more thing?"}
    )
    result = _render(staged, tmp_path, token=token, approval=approval, inquiry=edited)
    assert not result.ok
    assert result.reason is not None and "artifact hash mismatch" in result.reason
    assert not (tmp_path / "packets").exists() or not list((tmp_path / "packets").iterdir())
    assert _of(ledger, LedgerEventType.PACKET_RENDERED) == []


def test_expired_token_refused(staged, tmp_path: Path) -> None:
    _, _, _, _, clock = staged
    approval, token = _issue(staged, clock)
    clock.now = NOW + timedelta(hours=1)
    result = _render(staged, tmp_path, token=token, approval=approval)
    assert not result.ok
    assert result.reason is not None and "expired" in result.reason


def test_rerender_is_idempotent(staged, tmp_path: Path) -> None:
    ledger, _, _, _, clock = staged
    approval, token = _issue(staged, clock)
    first = _render(staged, tmp_path, token=token, approval=approval)
    second = _render(staged, tmp_path, token=token, approval=approval)
    assert first.ok and second.ok
    assert first.packet_hash == second.packet_hash
    assert first.packet_path == second.packet_path
    assert len(list((tmp_path / "packets").iterdir())) == 1
    assert len(_of(ledger, LedgerEventType.PACKET_RENDERED)) == 1


def test_inquiry_hash_binds_to_content(staged) -> None:
    _, _, _, inquiry, _ = staged
    same = inquiry.model_copy()
    assert inquiry_artifact_hash(inquiry) == inquiry_artifact_hash(same)
    for field_name, tweak in (
        ("proposed_question", "x?"),
        ("scope_rationale", "y"),
        ("supporting_evidence_ids", ["ev-other"]),
    ):
        edited = inquiry.model_copy(update={field_name: tweak})
        assert inquiry_artifact_hash(edited) != inquiry_artifact_hash(inquiry)


def test_golden_packet_snapshot(staged, tmp_path: Path) -> None:
    """The committed golden file is the exact packet for the fixture case + a fixed token."""
    from app.schemas.approval import ApprovalToken

    ledger, _, _, inquiry, clock = staged
    token = ApprovalToken(
        token_id="tok_golden000000000000000000000000",
        case_id=CASE_ID,
        artifact_hash=inquiry_artifact_hash(inquiry),
        action_type=ApprovalActionType.RENDER_INQUIRY_PACKET,
        reviewer_name=REVIEWER,
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=30),
    )
    approval = ApprovalService(clock=clock, ledger=ledger)
    result = _render(staged, tmp_path, token=token, approval=approval)
    assert result.ok, result.reason
    assert result.packet_path is not None
    assert Path(result.packet_path).read_text() == GOLDEN_PATH.read_text()
