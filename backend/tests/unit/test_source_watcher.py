"""MOO-721 watcher: incremental-only hits, honest no-hit runs, interval respected."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.enums import LedgerEventType
from app.repositories.cases import InMemoryLedger
from app.schemas.watch import WatchHitKind, WatchState
from app.services.corpus import load_corpus_manifest
from app.services.source_watcher import (
    SourceWatcher,
    expected_record_targets,
    watch_targets,
)
from tests.conftest import MANIFEST_PATH

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
MANIFEST = load_corpus_manifest(MANIFEST_PATH)
AMENDMENT = 74415

HISTORY_ROWS = [
    {"MatterHistoryId": 494274, "MatterHistoryActionName": "ADOPTED",
     "MatterHistoryActionDate": "2026-07-31T00:00:00", "MatterHistoryPassedFlagName": "Pass"},
    {"MatterHistoryId": 494395, "MatterHistoryActionName": "SIGNED",
     "MatterHistoryActionDate": "2026-08-03T00:00:00", "MatterHistoryPassedFlagName": None},
]
ATTACHMENT_ROWS = [
    {"MatterAttachmentId": 248735, "MatterAttachmentName": "Comptroller Review Letter",
     "MatterAttachmentHyperlink": "https://milwaukee.legistar1.com/milwaukee/attachments/x.pdf"},
]


class FakeStateStore:
    def __init__(self) -> None:
        self.states: dict[str, WatchState] = {}

    def get(self, key: str) -> WatchState | None:
        return self.states.get(key)

    def set(self, key: str, state: WatchState) -> None:
        self.states[key] = state


def _get_json_factory(histories=HISTORY_ROWS, attachments=ATTACHMENT_ROWS, status="Passed"):
    def get_json(url: str):
        if url.endswith("/histories"):
            return list(histories)
        if url.endswith("/attachments"):
            return list(attachments)
        if "$filter" in url:
            return []  # expected-record search: nothing published
        return {"MatterStatusName": status}

    return get_json


def _watcher(get_json, store, now=NOW):
    return SourceWatcher(get_json=get_json, state_store=store, clock=lambda: now)


def _ledger() -> InMemoryLedger:
    return InMemoryLedger(
        case_id=MANIFEST.case_id, clock=lambda: NOW, original_artifact_ids=frozenset()
    )


def test_watch_targets_are_derived_from_the_case_recipe() -> None:
    targets = watch_targets(MANIFEST)
    assert {t.matter_id for t in targets} == {68373, 71523, AMENDMENT}


def test_expected_record_target_comes_from_the_unpublished_artifact() -> None:
    targets = expected_record_targets(MANIFEST)
    assert len(targets) == 1
    assert targets[0].artifact_id == "tid-annual-report-2025"
    assert "Annual" in targets[0].search_words


def test_first_run_reports_unreviewed_actions_and_attachments() -> None:
    store, ledger = FakeStateStore(), _ledger()
    summary = _watcher(_get_json_factory(), store).check_case(MANIFEST, ledger)
    hits = [e for e in ledger.events() if e.event_type is LedgerEventType.WATCH_HIT]
    actions = [e for e in hits if e.watch_hit.kind is WatchHitKind.NEW_ACTION]
    # 3 watched matters × 2 history rows each (fake serves the same rows for all)
    assert len(actions) == 6
    adopted = [e for e in actions if e.watch_hit.action_name == "ADOPTED"]
    assert adopted and adopted[0].watch_hit.passed_flag == "Pass"
    assert summary["hits"] == len(hits)
    assert all(e.actor == "source-watcher" for e in hits)


def test_attachment_already_in_the_case_is_never_a_hit() -> None:
    store, ledger = FakeStateStore(), _ledger()
    known_id = next(
        e.legistar_attachment_id for e in MANIFEST.artifacts if e.legistar_attachment_id
    )
    rows = [{"MatterAttachmentId": known_id, "MatterAttachmentName": "Already reviewed",
             "MatterAttachmentHyperlink": "https://example.com/a.pdf"}]
    _watcher(_get_json_factory(attachments=rows), store).check_case(MANIFEST, ledger)
    attachment_hits = [
        e for e in ledger.events()
        if e.watch_hit and e.watch_hit.kind is WatchHitKind.NEW_ATTACHMENT
    ]
    assert attachment_hits == []


def test_second_run_is_incremental_zero_new_hits() -> None:
    store, ledger = FakeStateStore(), _ledger()
    get_json = _get_json_factory()
    _watcher(get_json, store).check_case(MANIFEST, ledger)
    first_count = len(ledger.events())
    later = NOW + timedelta(hours=2)
    summary = _watcher(get_json, store, now=later).check_case(MANIFEST, ledger)
    assert summary["hits"] == 0
    assert len(ledger.events()) == first_count
    key = f"{MANIFEST.case_id}--{AMENDMENT}"
    assert store.states[key].checked_at == later  # the no-hit run is still recorded


def test_one_new_action_produces_exactly_one_hit() -> None:
    store, ledger = FakeStateStore(), _ledger()
    _watcher(_get_json_factory(), store).check_case(MANIFEST, ledger)
    before = len(ledger.events())
    grown = [*HISTORY_ROWS, {"MatterHistoryId": 999999, "MatterHistoryActionName": "VETOED",
                             "MatterHistoryActionDate": "2026-09-01T00:00:00",
                             "MatterHistoryPassedFlagName": None}]
    later = NOW + timedelta(hours=2)
    summary = _watcher(_get_json_factory(histories=grown), store, now=later).check_case(
        MANIFEST, ledger
    )
    assert summary["hits"] == 3  # one per watched matter — the fake serves all three
    assert len(ledger.events()) == before + 3


def test_status_change_is_a_hit_only_after_a_baseline_exists() -> None:
    store, ledger = FakeStateStore(), _ledger()
    _watcher(_get_json_factory(status="In Committee"), store).check_case(MANIFEST, ledger)
    later = NOW + timedelta(hours=2)
    _watcher(_get_json_factory(status="Passed"), store, now=later).check_case(MANIFEST, ledger)
    changes = [
        e for e in ledger.events()
        if e.watch_hit and e.watch_hit.kind is WatchHitKind.STATUS_CHANGE
    ]
    assert len(changes) == 3
    assert changes[0].watch_hit.status_before == "In Committee"
    assert changes[0].watch_hit.status_after == "Passed"


def test_minimum_interval_skips_fresh_targets() -> None:
    store, ledger = FakeStateStore(), _ledger()
    calls: list[str] = []

    def counting_get_json(url: str):
        calls.append(url)
        return _get_json_factory()(url)

    _watcher(counting_get_json, store).check_case(MANIFEST, ledger)
    first_calls = len(calls)
    soon = NOW + timedelta(minutes=5)
    summary = _watcher(counting_get_json, store, now=soon).check_case(MANIFEST, ledger)
    assert summary == {"checked": 0, "skipped": 4, "hits": 0}
    assert len(calls) == first_calls  # not a single extra API call


def test_expected_record_candidate_is_reported_once_with_candidate_language() -> None:
    store, ledger = FakeStateStore(), _ledger()

    def get_json(url: str):
        if "$filter" in url and "Annual" in url:
            return [{"MatterId": 88001, "MatterFile": "260900",
                     "MatterTitle": "2025 Annual Report to the Common Council of TID projects"}]
        return _get_json_factory()(url)

    _watcher(get_json, store).check_case(MANIFEST, ledger)
    candidates = [
        e for e in ledger.events()
        if e.watch_hit and e.watch_hit.kind is WatchHitKind.EXPECTED_RECORD_CANDIDATE
    ]
    assert len(candidates) == 1
    assert candidates[0].watch_hit.expected_artifact_id == "tid-annual-report-2025"
    later = NOW + timedelta(hours=2)
    summary = _watcher(get_json, store, now=later).check_case(MANIFEST, ledger)
    assert summary["hits"] == 0  # the same candidate is never re-reported


def test_ledger_dedupe_is_the_second_belt_against_reruns() -> None:
    """Even with a wiped watermark, the ledger's stable event ids suppress duplicates."""
    store1, store2, ledger = FakeStateStore(), FakeStateStore(), _ledger()
    get_json = _get_json_factory()
    _watcher(get_json, store1).check_case(MANIFEST, ledger)
    count = len(ledger.events())
    summary = _watcher(get_json, store2).check_case(MANIFEST, ledger)  # fresh watermark
    assert summary["hits"] == 0
    assert len(ledger.events()) == count
