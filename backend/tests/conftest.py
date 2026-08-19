"""Shared test fixtures: the reviewed TID 121 replay corpus."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services.replay import ReplayOptions, replay_corpus

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "milwaukee-city-promise-ledger-demo-v1"
FIXTURE_EXTRACTION_PATH = FIXTURE_DIR / "fixture_extraction.json"


@pytest.fixture(scope="session")
def fixture_extraction_payload() -> dict:
    return json.loads(FIXTURE_EXTRACTION_PATH.read_text())


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_PATH = REPO_ROOT / "docs" / "sources" / "source-allowlist.yaml"
MANIFEST_PATH = REPO_ROOT / "docs" / "sources" / "corpus-manifest.yaml"

CASE_ID = "case-tid121-bronzeville-arts-tech-hub"
REPLAY_NOW = datetime(2026, 8, 19, 16, 0, tzinfo=UTC)


@pytest.fixture(scope="session")
def ledger_json(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, list]:
    """Replay the TID 121 corpus once per session: (ledger.json path, per-event results)."""
    base = tmp_path_factory.mktemp("replay")
    out = base / "ledger.json"
    report = replay_corpus(
        ReplayOptions(
            manifest_path=MANIFEST_PATH,
            allowlist_path=ALLOWLIST_PATH,
            extraction_path=FIXTURE_EXTRACTION_PATH,
            fixture_root=REPO_ROOT,
            vault_dir=base / "vault",
            out_path=out,
            replay_duplicate=True,
        ),
        clock=lambda: REPLAY_NOW,
    )
    return out, report.results
