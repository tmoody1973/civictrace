"""FastAPI assembly. Run: CIVICTRACE_LEDGER_JSON=/path/ledger.json uv run uvicorn app.main:app"""

from __future__ import annotations

import os
from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api import routes_approval, routes_artifacts, routes_cases, routes_health
from app.api.routes_approval import ApprovalGateway
from app.core.dependencies import (
    LEDGER_JSON_ENV,
    LIVE_ENV,
    JsonLedgerReader,
    TraceReader,
    cors_origins_from_env,
)
from app.schemas.api import ApiEnvelope


def create_app(
    *,
    trace_reader: TraceReader,
    approval: ApprovalGateway | None = None,
    cors_origins: Sequence[str] | None = None,
) -> FastAPI:
    app = FastAPI(title="CivicTrace API", version="0.1.0")
    app.state.trace_reader = trace_reader
    app.state.approval = approval
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_origins or cors_origins_from_env()),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["ETag", "X-CivicTrace-Content-Hash"],
    )
    app.include_router(routes_health.router)
    app.include_router(routes_cases.router)
    app.include_router(routes_artifacts.router)
    app.include_router(routes_approval.router)
    app.add_exception_handler(HTTPException, _http_error_as_envelope)  # type: ignore[arg-type]
    return app


def _http_error_as_envelope(_: Request, exc: HTTPException) -> JSONResponse:
    """Unmatched routes and framework errors use the same {ok,data,error} envelope."""
    envelope: ApiEnvelope[None] = ApiEnvelope(ok=False, data=None, error=str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump(mode="json"))


def _default_app() -> FastAPI | None:
    """Uvicorn entry point. Tests build their own app via create_app().

    CIVICTRACE_LIVE=1 replays the fixture corpus in-process and enables the
    approval/packet write endpoints. CIVICTRACE_LEDGER_JSON serves a static
    ledger read-only, as before.
    """
    if os.environ.get(LIVE_ENV):
        from app.services.approval_session import (
            DEFAULT_PACKET_DIR,
            ApprovalSession,
            default_replay_options,
        )

        session = ApprovalSession.from_replay(
            default_replay_options(), packet_dir=DEFAULT_PACKET_DIR
        )
        return create_app(trace_reader=session, approval=session)
    if os.environ.get(LEDGER_JSON_ENV):
        return create_app(trace_reader=JsonLedgerReader.from_env())
    return None


app = _default_app()
