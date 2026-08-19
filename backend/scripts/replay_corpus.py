#!/usr/bin/env python3
"""Replay the reviewed City corpus through the CivicTrace workflow. No model, no cloud, no network.

Usage (from backend/):
  uv run python scripts/replay_corpus.py ../docs/sources/corpus-manifest.yaml \
      --replay-duplicate --out /tmp/ledger.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.replay import ReplayOptions, replay_corpus  # noqa: E402

DEFAULT_ALLOWLIST = REPO_ROOT / "docs" / "sources" / "source-allowlist.yaml"
DEFAULT_EXTRACTION = (
    BACKEND_ROOT
    / "tests"
    / "fixtures"
    / "milwaukee-city-promise-ledger-demo-v1"
    / "fixture_extraction.json"
)
DEFAULT_VAULT = BACKEND_ROOT / ".local-artifacts" / "vault"


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    report = replay_corpus(
        ReplayOptions(
            manifest_path=args.manifest,
            allowlist_path=args.allowlist,
            extraction_path=args.extraction,
            fixture_root=REPO_ROOT,
            vault_dir=args.vault_dir,
            runner_kind=args.runner,
            out_path=args.out,
            replay_duplicate=args.replay_duplicate,
        )
    )
    for result in report.results:
        reason = (
            f"  — {result.reason[:80]}…"
            if result.reason and len(result.reason) > 80
            else (f"  — {result.reason}" if result.reason else "")
        )
        print(f"{result.artifact_id:28} {result.status:21} {result.job_key[:23]}…{reason}")
    print(report.case_outcome_line())
    print(f"ledger events: {len(report.ledger.events())}" + (f"  → {args.out}" if args.out else ""))
    return 0 if report.ok else 1


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--replay-duplicate",
        action="store_true",
        help="re-send the manifest's duplicate_event_fixture",
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="write ledger JSON here (for the API)"
    )
    parser.add_argument("--vault-dir", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--extraction", type=Path, default=DEFAULT_EXTRACTION)
    parser.add_argument(
        "--runner",
        choices=("fake", "adk"),
        default="fake",
        help=(
            "fake = reviewed fixtures (default, no credentials); adk = real Gemini Flash "
            "via Vertex AI (needs GOOGLE_CLOUD_PROJECT and local ADC sign-in)"
        ),
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
