"""Injectable data sources for the API. The API never touches the vault, a model, or a queue."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from app.schemas.case import LedgerEvent

LEDGER_JSON_ENV = "CIVICTRACE_LEDGER_JSON"


class TraceReader(Protocol):
    def events_for_case(self, case_id: str) -> list[LedgerEvent] | None: ...


class JsonLedgerReader:
    """Reads the ledger JSON written by scripts/replay_corpus.py."""

    def __init__(self, path: Path) -> None:
        payload = json.loads(path.read_text())
        self._case_id: str = payload["case_id"]
        self._events = [LedgerEvent.model_validate(raw) for raw in payload["events"]]

    @classmethod
    def from_env(cls) -> JsonLedgerReader:
        path = os.environ.get(LEDGER_JSON_ENV)
        if not path:
            raise RuntimeError(
                f"set {LEDGER_JSON_ENV} to a ledger.json from scripts/replay_corpus.py"
            )
        return cls(Path(path))

    def events_for_case(self, case_id: str) -> list[LedgerEvent] | None:
        return list(self._events) if case_id == self._case_id else None


class InMemoryTraceReader:
    def __init__(self, case_id: str, events: list[LedgerEvent]) -> None:
        self._case_id, self._events = case_id, events

    def events_for_case(self, case_id: str) -> list[LedgerEvent] | None:
        return list(self._events) if case_id == self._case_id else None
