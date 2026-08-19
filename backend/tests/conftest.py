"""Shared test fixtures: the reviewed TID 121 replay corpus."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "milwaukee-city-promise-ledger-demo-v1"
FIXTURE_EXTRACTION_PATH = FIXTURE_DIR / "fixture_extraction.json"


@pytest.fixture(scope="session")
def fixture_extraction_payload() -> dict:
    return json.loads(FIXTURE_EXTRACTION_PATH.read_text())


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_PATH = REPO_ROOT / "docs" / "sources" / "source-allowlist.yaml"
MANIFEST_PATH = REPO_ROOT / "docs" / "sources" / "corpus-manifest.yaml"
