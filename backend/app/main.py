"""FastAPI assembly. Run: CIVICTRACE_LEDGER_JSON=/path/ledger.json uv run uvicorn app.main:app"""

from __future__ import annotations

import os

from fastapi import FastAPI

from app.api import routes_cases, routes_health
from app.core.dependencies import LEDGER_JSON_ENV, JsonLedgerReader, TraceReader


def create_app(*, trace_reader: TraceReader) -> FastAPI:
    app = FastAPI(title="CivicTrace API", version="0.1.0")
    app.state.trace_reader = trace_reader
    app.include_router(routes_health.router)
    app.include_router(routes_cases.router)
    return app


def _default_app() -> FastAPI | None:
    """Uvicorn entry point. Tests build their own app via create_app()."""
    return (
        create_app(trace_reader=JsonLedgerReader.from_env())
        if os.environ.get(LEDGER_JSON_ENV)
        else None
    )


app = _default_app()
