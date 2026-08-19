"""Read-only case endpoints. # ponytail: add user auth before any deploy."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.dependencies import TraceReader
from app.schemas.api import ApiEnvelope, CaseSummaryView, TraceResponse
from app.services.trace import build_case_summary, build_trace

router = APIRouter()


@router.get("/cases/{case_id}/trace", response_model=ApiEnvelope[TraceResponse])
def case_trace(case_id: str, request: Request) -> ApiEnvelope[TraceResponse] | JSONResponse:
    reader: TraceReader = request.app.state.trace_reader
    events = reader.events_for_case(case_id)
    if events is None:
        envelope: ApiEnvelope[TraceResponse] = ApiEnvelope(
            ok=False, data=None, error=f"case {case_id!r} not found"
        )
        return JSONResponse(status_code=404, content=envelope.model_dump(mode="json"))
    return ApiEnvelope(ok=True, data=build_trace(case_id, events), error=None)


@router.get("/cases/{case_id}", response_model=ApiEnvelope[CaseSummaryView])
def case_summary(case_id: str, request: Request) -> ApiEnvelope[CaseSummaryView] | JSONResponse:
    reader: TraceReader = request.app.state.trace_reader
    events = reader.events_for_case(case_id)
    if events is None:
        envelope: ApiEnvelope[CaseSummaryView] = ApiEnvelope(
            ok=False, data=None, error=f"case {case_id!r} not found"
        )
        return JSONResponse(status_code=404, content=envelope.model_dump(mode="json"))
    summary = build_case_summary(case_id, reader.case_topic(case_id), events)
    return ApiEnvelope(ok=True, data=summary, error=None)
