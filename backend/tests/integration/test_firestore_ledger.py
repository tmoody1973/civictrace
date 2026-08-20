"""FirestoreLedger against the emulator: same event chain, same ids, append-only.

Skipped cleanly when FIRESTORE_EMULATOR_HOST is unset. Run locally with:
  docker run --rm -p 8686:8686 gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators \
    gcloud emulators firestore start --host-port=0.0.0.0:8686
  FIRESTORE_EMULATOR_HOST=localhost:8686 uv run pytest tests/integration/test_firestore_ledger.py
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.services.corpus import load_corpus_manifest
from app.services.replay import ReplayOptions, build_workflow
from tests.conftest import ALLOWLIST_PATH, FIXTURE_DIR, MANIFEST_PATH, REPO_ROOT

pytestmark = pytest.mark.skipif(
    not os.environ.get("FIRESTORE_EMULATOR_HOST"),
    reason="Firestore emulator not running (set FIRESTORE_EMULATOR_HOST)",
)

NOW = datetime(2026, 8, 19, 18, 0, tzinfo=UTC)


def _options(tmp_path: Path) -> ReplayOptions:
    return ReplayOptions(
        manifest_path=MANIFEST_PATH,
        allowlist_path=ALLOWLIST_PATH,
        extraction_path=FIXTURE_DIR / "fixture_extraction.json",
        fixture_root=REPO_ROOT,
        vault_dir=tmp_path / "vault",
    )


def _firestore_ledger(manifest):  # noqa: ANN001, ANN202
    from google.cloud import firestore

    from app.repositories.firestore_cases import FirestoreLedger

    client = firestore.Client(project="civictrace-emulator-test")
    return FirestoreLedger(
        client=client,
        # Unique per test run: the emulator keeps state for its lifetime.
        case_id=f"{manifest.case_id}-{uuid.uuid4().hex[:8]}",
        case_topic=manifest.case_topic,
        original_artifact_ids=frozenset(
            entry.artifact_id for entry in manifest.artifacts if entry.role == "original_commitment"
        ),
        clock=lambda: NOW,
    )


def _replay(tmp_path: Path, ledger=None):  # noqa: ANN001, ANN202
    manifest = load_corpus_manifest(MANIFEST_PATH)
    workflow, used_ledger, _ = build_workflow(
        manifest, _options(tmp_path), clock=lambda: NOW, ledger=ledger
    )
    for index, entry in enumerate(manifest.artifacts):
        asyncio.run(workflow.run(manifest.source_event(entry.artifact_id), trace_id=f"t-{index}"))
    return used_ledger


def test_firestore_replay_matches_in_memory_chain(tmp_path: Path) -> None:
    manifest = load_corpus_manifest(MANIFEST_PATH)
    in_memory = _replay(tmp_path / "mem")
    cloud = _replay(tmp_path / "fs", ledger=_firestore_ledger(manifest))
    memory_events = in_memory.events()
    cloud_events = cloud.events()
    assert [e.event_type for e in cloud_events] == [e.event_type for e in memory_events]
    # Same job keys + payloads → same derived ids, except the case-scoped payloads that
    # embed the (unique, per-run) case id.
    assert [e.payload_ref for e in cloud_events if "case" not in e.payload_ref] == [
        e.payload_ref for e in memory_events if "case" not in e.payload_ref
    ]


def test_duplicate_append_is_suppressed(tmp_path: Path) -> None:
    from app.repositories.cases import AppendOutcome

    manifest = load_corpus_manifest(MANIFEST_PATH)
    ledger = _firestore_ledger(manifest)
    workflow, _, _ = build_workflow(manifest, _options(tmp_path), clock=lambda: NOW, ledger=ledger)
    for index, entry in enumerate(manifest.artifacts):
        asyncio.run(workflow.run(manifest.source_event(entry.artifact_id), trace_id=f"t-{index}"))
    before = ledger.events()

    # Ledger-level: re-appending an existing event is refused by the database itself.
    assert ledger.append(before[0]) is AppendOutcome.DUPLICATE_SUPPRESSED
    # Workflow-level: the same source event again is a no-op on the same workflow.
    asyncio.run(workflow.run(manifest.source_event("tid121-project-plan-2024"), trace_id="again"))
    assert [e.event_id for e in ledger.events()] == [e.event_id for e in before]


def test_ledger_has_no_update_or_delete(tmp_path: Path) -> None:
    from app.repositories.firestore_cases import FirestoreLedger

    forbidden = [name for name in dir(FirestoreLedger) if "update" in name or "delete" in name]
    assert forbidden == []
