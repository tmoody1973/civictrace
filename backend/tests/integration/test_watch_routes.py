"""MOO-721 watch endpoints: recorded watermarks out, one gated run in, honest 503s."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.routes_watch import WatchGateway
from app.core.dependencies import InMemoryTraceReader
from app.main import create_app
from app.schemas.watch import WatchState

NOW = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)


def _app(with_watch: bool = True):
    watch = None
    if with_watch:
        state = WatchState(
            case_id="case-tid121",
            matter_id=74415,
            legistar_file="260433",
            matter_status="Passed",
            checked_at=NOW,
        )
        watch = WatchGateway(
            states_for_case=lambda case_id: [state] if case_id == "case-tid121" else [],
            start_run=lambda: "watch-run-202608271200",
        )
    return create_app(trace_reader=InMemoryTraceReader("case-tid121", []), watch=watch)


def test_watch_status_returns_recorded_watermarks() -> None:
    client = TestClient(_app())
    body = client.get("/cases/case-tid121/watch").json()
    assert body["ok"] is True
    target = body["data"]["targets"][0]
    assert target["matter_id"] == 74415
    assert target["checked_at"] == "2026-08-27T12:00:00Z"


def test_watch_status_for_unwatched_case_is_an_honest_empty_list() -> None:
    client = TestClient(_app())
    body = client.get("/cases/case-unknown/watch").json()
    assert body["ok"] is True and body["data"]["targets"] == []


def test_watch_run_enqueues_and_returns_the_run_id() -> None:
    client = TestClient(_app())
    body = client.post("/watch/run").json()
    assert body["ok"] is True and body["data"]["run"].startswith("watch-run-")


def test_endpoints_say_so_when_the_watcher_is_not_enabled() -> None:
    client = TestClient(_app(with_watch=False))
    assert client.get("/cases/x/watch").status_code == 503
    assert client.post("/watch/run").status_code == 503
