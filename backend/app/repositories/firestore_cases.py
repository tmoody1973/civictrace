"""Firestore-backed Promise Ledger (Slice 5.2, MOO-708). Append-only, like everything else.

Layout (stack-decision doc §5): `cases/{case_id}` holds the running counter and topic;
`cases/{case_id}/ledger_events/{event_id}` holds one immutable event each. The document id
IS the derived event id, so re-appending the same fact hits an existing document and is
suppressed — the same guarantee the in-memory ledger gives, enforced by the database.

Ordering uses a per-case `seq` assigned in a transaction. A single-field order_by on a
subcollection uses Firestore's automatic index — no composite index is required, which is
why `infra/terraform` defines none for this module.

# ponytail: sync Firestore client called from async workflow methods; acceptable for the
# single-event worker requests of the MVP. Move to the async client if throughput matters.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from google.cloud import firestore

from app.repositories.cases import AppendOutcome, LedgerRecorder
from app.schemas.case import LedgerEvent

CASES_COLLECTION = "cases"
EVENTS_SUBCOLLECTION = "ledger_events"


class FirestoreLedger(LedgerRecorder):
    def __init__(
        self,
        *,
        client: firestore.Client,
        case_id: str,
        clock: Callable[[], datetime],
        original_artifact_ids: frozenset[str],
        case_topic: str = "",
    ) -> None:
        super().__init__(
            case_id=case_id,
            clock=clock,
            original_artifact_ids=original_artifact_ids,
            case_topic=case_topic,
        )
        self._client = client
        self._case_ref = client.collection(CASES_COLLECTION).document(case_id)
        self._events_ref = self._case_ref.collection(EVENTS_SUBCOLLECTION)

    def append(self, event: LedgerEvent) -> AppendOutcome:
        transaction = self._client.transaction()
        outcome = _append_once(
            transaction,
            case_ref=self._case_ref,
            event_ref=self._events_ref.document(event.event_id),
            case_fields={"case_id": self._case_id, "case_topic": self._case_topic},
            payload=event.model_dump(mode="json"),
        )
        return AppendOutcome(outcome)

    def events(self) -> list[LedgerEvent]:
        documents = self._events_ref.order_by("seq").stream()
        return [LedgerEvent.model_validate(doc.to_dict()["event"]) for doc in documents]


@firestore.transactional
def _append_once(
    transaction: firestore.Transaction,
    *,
    case_ref: firestore.DocumentReference,
    event_ref: firestore.DocumentReference,
    case_fields: dict[str, str],
    payload: dict[str, Any],
) -> str:
    """Reads before writes, per Firestore transaction rules; create() makes append-only real."""
    if event_ref.get(transaction=transaction).exists:
        return AppendOutcome.DUPLICATE_SUPPRESSED
    case_snapshot = case_ref.get(transaction=transaction)
    current = case_snapshot.to_dict() if case_snapshot.exists else None
    sequence = int((current or {}).get("event_count", 0)) + 1
    transaction.set(case_ref, {**case_fields, "event_count": sequence}, merge=True)
    transaction.create(event_ref, {"seq": sequence, "event": payload})
    return AppendOutcome.APPENDED
