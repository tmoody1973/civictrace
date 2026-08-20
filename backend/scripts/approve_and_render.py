#!/usr/bin/env python3
"""Replay the corpus, issue one human approval token, render the DRAFT inquiry packet.

Usage (from backend/):
  uv run python scripts/approve_and_render.py --reviewer "Tarik Moody"
  uv run python scripts/approve_and_render.py --reviewer "Tarik Moody" --tamper

--tamper edits the inquiry AFTER the token is issued, proving the hash binding
fails closed: APPROVAL_REFUSED, no packet file.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.domain.enums import ApprovalActionType, LedgerEventType  # noqa: E402
from app.services.approval import ApprovalService  # noqa: E402
from app.services.packet import (  # noqa: E402
    find_staged_delta,
    find_staged_inquiry,
    inquiry_artifact_hash,
    render_inquiry_packet,
)
from app.services.replay import ReplayOptions, replay_corpus  # noqa: E402

DEFAULT_EXTRACTION = (
    BACKEND_ROOT
    / "tests"
    / "fixtures"
    / "milwaukee-city-promise-ledger-demo-v1"
    / "fixture_extraction.json"
)
DEFAULT_OUT_DIR = BACKEND_ROOT / ".local-artifacts" / "packets"


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    report = replay_corpus(
        ReplayOptions(
            manifest_path=REPO_ROOT / "docs" / "sources" / "corpus-manifest.yaml",
            allowlist_path=REPO_ROOT / "docs" / "sources" / "source-allowlist.yaml",
            extraction_path=DEFAULT_EXTRACTION,
            fixture_root=REPO_ROOT,
            vault_dir=BACKEND_ROOT / ".local-artifacts" / "vault",
        )
    )
    print(report.case_outcome_line())
    events = report.ledger.events()
    delta, inquiry = find_staged_delta(events), find_staged_inquiry(events)
    bundle = report.ledger.build_case_bundle(trigger_artifact_id="", new_evidence_ids=[])

    approval = ApprovalService(clock=lambda: datetime.now(UTC), ledger=report.ledger)
    token = approval.issue(
        case_id=delta.case_id,
        artifact_hash=inquiry_artifact_hash(inquiry),
        action_type=ApprovalActionType.RENDER_INQUIRY_PACKET,
        reviewer_name=args.reviewer,
    )
    print(f"token issued: {token.token_id}  reviewer={token.reviewer_name}")
    print(f"approved inquiry hash: {token.artifact_hash}")

    if args.tamper:
        inquiry = inquiry.model_copy(
            update={"proposed_question": inquiry.proposed_question + " Edited after approval."}
        )
        print("inquiry EDITED after approval (tamper demo)")

    result = render_inquiry_packet(
        bundle=bundle,
        delta=delta,
        inquiry=inquiry,
        events=events,
        token=token,
        approval=approval,
        ledger=report.ledger,
        out_dir=args.out_dir,
    )
    if not result.ok:
        print(f"REFUSED: {result.reason}")
        refused = [
            e for e in report.ledger.events() if e.event_type is LedgerEventType.APPROVAL_REFUSED
        ]
        print(f"ledger APPROVAL_REFUSED rows: {len(refused)}  (no packet file written)")
        return 1
    print(f"packet rendered: {result.packet_path}")
    print(f"packet hash: {result.packet_hash}")
    return 0


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer", required=True, help="Typed reviewer name (Slice 5 adds auth)")
    parser.add_argument("--tamper", action="store_true", help="Edit the inquiry after approval")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
