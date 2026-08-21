"""Read-only multi-case TraceReader over Firestore (MOO-719).

The API reads ANY case this way — the reviewed demo case and journalist-intake cases
alike. Writes still go through the per-case FirestoreLedger; approval endpoints keep
their own gateway. # ponytail: full scans per request; fine for a handful of demo
cases, add per-case caching if case count grows.
"""

from __future__ import annotations

from typing import Any

from app.domain.enums import LedgerEventType
from app.repositories.firestore_cases import CASES_COLLECTION, EVENTS_SUBCOLLECTION
from app.schemas.case import LedgerEvent
from app.schemas.source import Artifact


class FirestoreTraceReader:
    def __init__(self, client: Any) -> None:
        self._client = client
        self._cases = client.collection(CASES_COLLECTION)

    def case_ids(self) -> list[str]:
        return sorted(doc.id for doc in self._cases.stream())

    def events_for_case(self, case_id: str) -> list[LedgerEvent] | None:
        case_ref = self._cases.document(case_id)
        if not case_ref.get().exists:
            return None
        documents = case_ref.collection(EVENTS_SUBCOLLECTION).order_by("seq").stream()
        return [LedgerEvent.model_validate(doc.to_dict()["event"]) for doc in documents]

    def case_topic(self, case_id: str) -> str:
        snapshot = self._cases.document(case_id).get()
        data = snapshot.to_dict() if snapshot.exists else None
        return str((data or {}).get("case_topic", ""))

    def artifact(self, artifact_id: str) -> Artifact | None:
        for case_id in self.case_ids():
            for event in self.events_for_case(case_id) or []:
                if (
                    event.artifact is not None
                    and event.artifact.artifact_id == artifact_id
                    and event.event_type
                    in (LedgerEventType.ARTIFACT_STORED, LedgerEventType.ARTIFACT_NOT_PUBLISHED)
                ):
                    return event.artifact
        return None
