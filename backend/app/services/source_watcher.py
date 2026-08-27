"""Source watcher (Slice 8.1, MOO-721). Deterministic, read-only, bounded.

A scheduled run asks the official Legistar record, for each case: (a) anything new on
the matters this case watches — history actions, attachments, status — and (b) for an
expected-but-unpublished record, whether a matching matter now exists (a CANDIDATE,
never a confirmed link). Hits are verbatim observations written to the case ledger with
full provenance; the human intake gate stands between a hit and case evidence. A no-hit
run updates checked_at and nothing else. No model is involved anywhere in this module.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol

from app.domain.enums import LedgerEventType
from app.repositories.cases import AppendOutcome, LedgerRecorder, ledger_event_id
from app.schemas.case import LedgerEvent
from app.schemas.corpus import CorpusManifest
from app.schemas.watch import WatchHit, WatchHitKind, WatchState, watch_state_key
from app.services.legistar_intake import LEGISTAR_BASE, _search_words

logger = logging.getLogger("civictrace.watcher")

WATCH_ACTOR = "source-watcher"
EXPECTED_ROLE = "expected_later_evidence"
EXPECTED_SEARCH_LIMIT = 5
DEFAULT_MINIMUM_INTERVAL_MINUTES = 60


@dataclass(frozen=True)
class WatchTarget:
    """One watched Legistar matter, derived from a case recipe — never configured by hand."""

    case_id: str
    matter_id: int
    legistar_file: str | None


@dataclass(frozen=True)
class ExpectedRecordTarget:
    """An expected-but-unpublished artifact the case is waiting for (e.g. an annual report)."""

    case_id: str
    artifact_id: str
    search_words: tuple[str, ...]


class WatchStateStore(Protocol):
    def get(self, key: str) -> WatchState | None: ...
    def set(self, key: str, state: WatchState) -> None: ...


def watch_targets(manifest: CorpusManifest) -> list[WatchTarget]:
    seen: set[int] = set()
    targets = []
    for entry in manifest.artifacts:
        if entry.legistar_matter_id is None or entry.legistar_matter_id in seen:
            continue
        seen.add(entry.legistar_matter_id)
        targets.append(
            WatchTarget(
                case_id=manifest.case_id,
                matter_id=entry.legistar_matter_id,
                legistar_file=entry.legistar_file,
            )
        )
    return targets


def expected_record_targets(manifest: CorpusManifest) -> list[ExpectedRecordTarget]:
    targets = []
    for entry in manifest.artifacts:
        if entry.role != EXPECTED_ROLE or entry.legistar_matter_id is not None:
            continue
        words = tuple(_search_words(entry.title or entry.artifact_id))
        if words:
            targets.append(
                ExpectedRecordTarget(
                    case_id=manifest.case_id,
                    artifact_id=entry.artifact_id,
                    search_words=words,
                )
            )
    return targets


class SourceWatcher:
    """Check one case recipe against the live official record and ledger the differences."""

    def __init__(
        self,
        *,
        get_json: Callable[[str], Any],
        state_store: WatchStateStore,
        clock: Callable[[], datetime],
        minimum_interval_minutes: int = DEFAULT_MINIMUM_INTERVAL_MINUTES,
    ) -> None:
        self._get_json = get_json
        self._states = state_store
        self._clock = clock
        self._minimum_interval = timedelta(minutes=minimum_interval_minutes)

    def check_case(self, manifest: CorpusManifest, ledger: LedgerRecorder) -> dict[str, int]:
        """Returns a small summary: targets checked/skipped and hits appended."""
        summary = {"checked": 0, "skipped": 0, "hits": 0}
        known_attachment_ids = {
            entry.legistar_attachment_id
            for entry in manifest.artifacts
            if entry.legistar_attachment_id is not None
        }
        for target in watch_targets(manifest):
            key = watch_state_key(target.case_id, target.matter_id)
            state = self._states.get(key)
            if self._too_soon(state):
                summary["skipped"] += 1
                continue
            hits, new_state = self._check_matter(target, state, known_attachment_ids)
            summary["checked"] += 1
            summary["hits"] += self._append_hits(ledger, target.case_id, hits)
            self._states.set(key, new_state)
        for expected in expected_record_targets(manifest):
            key = watch_state_key(expected.case_id, None, suffix=expected.artifact_id)
            state = self._states.get(key)
            if self._too_soon(state):
                summary["skipped"] += 1
                continue
            hits, new_state = self._check_expected(expected, state)
            summary["checked"] += 1
            summary["hits"] += self._append_hits(ledger, expected.case_id, hits)
            self._states.set(key, new_state)
        return summary

    def _too_soon(self, state: WatchState | None) -> bool:
        return (
            state is not None
            and state.checked_at is not None
            and self._clock() - state.checked_at < self._minimum_interval
        )

    def _check_matter(
        self,
        target: WatchTarget,
        state: WatchState | None,
        known_attachment_ids: set[int],
    ) -> tuple[list[WatchHit], WatchState]:
        matter_url = f"{LEGISTAR_BASE}/matters/{target.matter_id}"
        matter = self._get_json(matter_url)
        histories = self._get_json(f"{matter_url}/histories")
        attachments = self._get_json(f"{matter_url}/attachments")
        now = self._clock()
        status = (matter or {}).get("MatterStatusName")
        seen_history = set(state.seen_history_ids) if state else set()
        seen_attachments = set(state.seen_attachment_ids) if state else set()
        hits: list[WatchHit] = []

        for row in histories if isinstance(histories, list) else []:
            history_id = int(row["MatterHistoryId"])
            if history_id in seen_history:
                continue
            hits.append(
                WatchHit(
                    kind=WatchHitKind.NEW_ACTION,
                    case_id=target.case_id,
                    matter_id=target.matter_id,
                    legistar_file=target.legistar_file,
                    observed_at=now,
                    source_url=f"{matter_url}/histories",
                    history_id=history_id,
                    action_name=row.get("MatterHistoryActionName"),
                    action_date=row.get("MatterHistoryActionDate"),
                    passed_flag=row.get("MatterHistoryPassedFlagName"),
                )
            )
            seen_history.add(history_id)

        for row in attachments if isinstance(attachments, list) else []:
            attachment_id = int(row["MatterAttachmentId"])
            if attachment_id in seen_attachments or attachment_id in known_attachment_ids:
                continue
            hits.append(
                WatchHit(
                    kind=WatchHitKind.NEW_ATTACHMENT,
                    case_id=target.case_id,
                    matter_id=target.matter_id,
                    legistar_file=target.legistar_file,
                    observed_at=now,
                    source_url=f"{matter_url}/attachments",
                    attachment_id=attachment_id,
                    attachment_name=row.get("MatterAttachmentName"),
                    attachment_url=row.get("MatterAttachmentHyperlink"),
                )
            )
            seen_attachments.add(attachment_id)

        if state is not None and state.matter_status and status != state.matter_status:
            hits.append(
                WatchHit(
                    kind=WatchHitKind.STATUS_CHANGE,
                    case_id=target.case_id,
                    matter_id=target.matter_id,
                    legistar_file=target.legistar_file,
                    observed_at=now,
                    source_url=matter_url,
                    status_before=state.matter_status,
                    status_after=status,
                )
            )

        new_state = WatchState(
            case_id=target.case_id,
            matter_id=target.matter_id,
            legistar_file=target.legistar_file,
            seen_history_ids=sorted(seen_history),
            seen_attachment_ids=sorted(seen_attachments | known_attachment_ids),
            matter_status=status,
            checked_at=now,
        )
        return hits, new_state

    def _check_expected(
        self, expected: ExpectedRecordTarget, state: WatchState | None
    ) -> tuple[list[WatchHit], WatchState]:
        import urllib.parse

        per_word = [
            f"(substringof('{word}',MatterTitle) or substringof('{word}',MatterName))"
            for word in expected.search_words
        ]
        query = urllib.parse.quote(" and ".join(per_word))
        url = (
            f"{LEGISTAR_BASE}/matters?$filter={query}"
            f"&$orderby=MatterIntroDate%20desc&$top={EXPECTED_SEARCH_LIMIT}"
        )
        rows = self._get_json(url)
        now = self._clock()
        seen = set(state.seen_candidate_matter_ids) if state else set()
        hits: list[WatchHit] = []
        for row in rows if isinstance(rows, list) else []:
            matter_id = int(row["MatterId"])
            if matter_id in seen:
                continue
            hits.append(
                WatchHit(
                    kind=WatchHitKind.EXPECTED_RECORD_CANDIDATE,
                    case_id=expected.case_id,
                    matter_id=matter_id,
                    legistar_file=str(row.get("MatterFile") or "") or None,
                    observed_at=now,
                    source_url=url,
                    expected_artifact_id=expected.artifact_id,
                    candidate_title=row.get("MatterTitle") or row.get("MatterName"),
                )
            )
            seen.add(matter_id)
        new_state = WatchState(
            case_id=expected.case_id,
            matter_id=None,
            seen_candidate_matter_ids=sorted(seen),
            checked_at=now,
        )
        return hits, new_state

    def _append_hits(
        self, ledger: LedgerRecorder, case_id: str, hits: Iterable[WatchHit]
    ) -> int:
        appended = 0
        job_key = f"watch-{case_id}"  # stable: the ledger's event-id dedupe is the second belt
        for hit in hits:
            event = LedgerEvent(
                event_id=ledger_event_id(job_key, LedgerEventType.WATCH_HIT, hit.payload_ref()),
                case_id=case_id,
                job_key=job_key,
                event_type=LedgerEventType.WATCH_HIT,
                payload_ref=hit.payload_ref(),
                occurred_at=hit.observed_at,
                actor=WATCH_ACTOR,
                watch_hit=hit,
            )
            if ledger.append(event) is AppendOutcome.APPENDED:
                appended += 1
        return appended
