"""Watch-state watermarks in Firestore (MOO-721). One doc per (case, watched matter).

The watermark records what the watcher has already reported and when it last checked —
so absence of news is a recorded fact ("checked at 12:00, nothing new"), never an
inference, and a rerun can never re-report the same official action.
"""

from __future__ import annotations

from typing import Any

from app.schemas.watch import WatchState

WATCH_STATE_COLLECTION = "watch_state"


class FirestoreWatchStore:
    def __init__(self, client: Any) -> None:
        self._collection = client.collection(WATCH_STATE_COLLECTION)

    def get(self, key: str) -> WatchState | None:
        snapshot = self._collection.document(key).get()
        if not snapshot.exists:
            return None
        return WatchState.model_validate(snapshot.to_dict())

    def set(self, key: str, state: WatchState) -> None:
        self._collection.document(key).set(state.model_dump(mode="json"))

    def states_for_case(self, case_id: str) -> list[WatchState]:
        query = self._collection.where("case_id", "==", case_id)
        return [WatchState.model_validate(doc.to_dict()) for doc in query.stream()]
