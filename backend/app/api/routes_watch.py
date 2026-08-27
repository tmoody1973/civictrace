"""Watch endpoints (MOO-721): what the watcher knows, and a gated "check now".

GET /cases/{case_id}/watch returns the recorded watermarks — when the official record
was last checked, per watched matter. Hits themselves live in the case ledger (trace).
POST /watch/run enqueues ONE bounded worker task; it never runs checks in-request.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.schemas.api import ApiEnvelope
from app.schemas.watch import WatchState

router = APIRouter()


class WatchGateway:
    def __init__(
        self,
        *,
        states_for_case: Callable[[str], list[WatchState]],
        start_run: Callable[[], str],
    ) -> None:
        self.states_for_case = states_for_case
        self.start_run = start_run


class WatchStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    targets: list[WatchState]


@router.get("/cases/{case_id}/watch", response_model=ApiEnvelope[WatchStatus])
def watch_status(case_id: str, request: Request) -> ApiEnvelope[WatchStatus] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, "the source watcher is not enabled on this server")
    states = gateway.states_for_case(case_id)
    return ApiEnvelope(ok=True, data=WatchStatus(case_id=case_id, targets=states), error=None)


@router.post("/watch/run", response_model=ApiEnvelope[dict])
def watch_run(request: Request) -> ApiEnvelope[dict] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, "the source watcher is not enabled on this server")
    run_id = gateway.start_run()
    return ApiEnvelope(ok=True, data={"run": run_id}, error=None)


def _gateway(request: Request) -> WatchGateway | None:
    return getattr(request.app.state, "watch", None)


def _error(status_code: int, message: str) -> JSONResponse:
    envelope: ApiEnvelope[None] = ApiEnvelope(ok=False, data=None, error=message)
    return JSONResponse(status_code=status_code, content=envelope.model_dump(mode="json"))
