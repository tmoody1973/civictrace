"""Injectable data sources for the API. The API never touches the vault, a model, or a queue."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from app.domain.enums import LedgerEventType
from app.schemas.case import LedgerEvent
from app.schemas.source import Artifact

LEDGER_JSON_ENV = "CIVICTRACE_LEDGER_JSON"
LIVE_ENV = "CIVICTRACE_LIVE"
CORS_ORIGINS_ENV = "CIVICTRACE_CORS_ORIGINS"
DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)


def cors_origins_from_env() -> tuple[str, ...]:
    raw = os.environ.get(CORS_ORIGINS_ENV, "")
    origins = tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    return origins or DEFAULT_CORS_ORIGINS


class TraceReader(Protocol):
    def case_ids(self) -> list[str]: ...
    def events_for_case(self, case_id: str) -> list[LedgerEvent] | None: ...
    def case_topic(self, case_id: str) -> str: ...
    def artifact(self, artifact_id: str) -> Artifact | None:
        """The ledger's record of one artifact (stored or not published); None if never seen."""
        ...


def _artifact_from_events(events: list[LedgerEvent], artifact_id: str) -> Artifact | None:
    recorded = (
        event.artifact
        for event in events
        if event.artifact is not None
        and event.artifact.artifact_id == artifact_id
        and event.event_type
        in (LedgerEventType.ARTIFACT_STORED, LedgerEventType.ARTIFACT_NOT_PUBLISHED)
    )
    return next(recorded, None)


class JsonLedgerReader:
    """Reads the ledger JSON written by scripts/replay_corpus.py."""

    def __init__(self, path: Path) -> None:
        payload = json.loads(path.read_text())
        self._case_id: str = payload["case_id"]
        self._case_topic: str = payload.get("case_topic", "")
        self._events = [LedgerEvent.model_validate(raw) for raw in payload["events"]]

    @classmethod
    def from_env(cls) -> JsonLedgerReader:
        path = os.environ.get(LEDGER_JSON_ENV)
        if not path:
            raise RuntimeError(
                f"set {LEDGER_JSON_ENV} to a ledger.json from scripts/replay_corpus.py"
            )
        return cls(Path(path))

    def case_ids(self) -> list[str]:
        return [self._case_id] if self._events else []

    def events_for_case(self, case_id: str) -> list[LedgerEvent] | None:
        return list(self._events) if case_id == self._case_id else None

    def case_topic(self, case_id: str) -> str:
        return self._case_topic

    def artifact(self, artifact_id: str) -> Artifact | None:
        return _artifact_from_events(self._events, artifact_id)


class InMemoryTraceReader:
    def __init__(self, case_id: str, events: list[LedgerEvent], case_topic: str = "") -> None:
        self._case_id, self._events, self._case_topic = case_id, events, case_topic

    def case_ids(self) -> list[str]:
        return [self._case_id] if self._events else []

    def events_for_case(self, case_id: str) -> list[LedgerEvent] | None:
        return list(self._events) if case_id == self._case_id else None

    def case_topic(self, case_id: str) -> str:
        return self._case_topic

    def artifact(self, artifact_id: str) -> Artifact | None:
        return _artifact_from_events(self._events, artifact_id)
