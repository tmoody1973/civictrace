"""FastAPI assembly. Run: CIVICTRACE_LEDGER_JSON=/path/ledger.json uv run uvicorn app.main:app"""

from __future__ import annotations

import os
import secrets
from collections.abc import Sequence

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api import (
    routes_approval,
    routes_artifacts,
    routes_cases,
    routes_health,
    routes_intake,
    routes_transcripts,
)
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
    intake: object | None = None,
    cors_origins: Sequence[str] | None = None,
    bearer_token: str | None = None,
    uri_resolver: object | None = None,
) -> FastAPI:
    app = FastAPI(title="CivicTrace API", version="0.1.0")
    app.state.trace_reader = trace_reader
    app.state.approval = approval
    app.state.intake = intake
    if uri_resolver is not None:
        app.state.uri_resolver = uri_resolver
    # strip(): secret values created with `openssl ... | gcloud secrets versions add`
    # carry a trailing newline; the header value never does.
    if bearer_token and bearer_token.strip():
        _require_bearer(app, bearer_token.strip())
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
    app.include_router(routes_transcripts.router)
    app.include_router(routes_intake.router)
    app.include_router(routes_approval.router)
    app.add_exception_handler(HTTPException, _http_error_as_envelope)  # type: ignore[arg-type]
    return app


def _require_bearer(app: FastAPI, token: str) -> None:
    """Every route except /healthz needs the shared bearer (Slice 5 cloud demo).

    # ponytail: shared token guards the public dev URL; per-user auth is post-hackathon.
    """

    @app.middleware("http")
    async def bearer_gate(request: Request, call_next):  # type: ignore[no-untyped-def]  # noqa: ANN202
        if request.url.path in ("/healthz", "/health") or request.method == "OPTIONS":
            return await call_next(request)
        supplied = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not supplied or not secrets.compare_digest(supplied, token):
            envelope: ApiEnvelope[None] = ApiEnvelope(
                ok=False, data=None, error="missing or wrong bearer token"
            )
            return JSONResponse(status_code=401, content=envelope.model_dump(mode="json"))
        return await call_next(request)


def _http_error_as_envelope(_: Request, exc: HTTPException) -> JSONResponse:
    """Unmatched routes and framework errors use the same {ok,data,error} envelope."""
    envelope: ApiEnvelope[None] = ApiEnvelope(ok=False, data=None, error=str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content=envelope.model_dump(mode="json"))


def _default_app() -> FastAPI | None:
    """Uvicorn entry point. Tests build their own app via create_app().

    CIVICTRACE_CLOUD=1 serves the Firestore-backed case with the bearer gate
    (Cloud Run api service). CIVICTRACE_LIVE=1 replays the fixture corpus
    in-process and enables the approval/packet write endpoints locally.
    CIVICTRACE_LEDGER_JSON serves a static ledger read-only, as before.
    """
    if os.environ.get("CIVICTRACE_CLOUD"):
        return _cloud_app()
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


def _cloud_app() -> FastAPI:
    from google.cloud import firestore  # noqa: I001
    from google.cloud import storage  # type: ignore[attr-defined]

    from app.api.routes_intake import IntakeGateway
    from app.repositories.firestore_trace_reader import FirestoreTraceReader
    from app.repositories.intake import FirestoreIntakeStore
    from app.services.approval_session import ApprovalSession
    from app.services.cloud import CloudConfig, build_cloud_ledger
    from app.services.cloud_intake import CreateCaseEnqueuer
    from app.services.corpus import load_corpus_manifest
    from app.services.legistar_intake import LegistarIntakeClient
    from app.services.packet_store import GcsPacketWriter
    from app.services.uri_bytes import GcsUriResolver

    config = CloudConfig.from_env()
    manifest = load_corpus_manifest(config.manifest_path)
    storage_client = storage.Client(project=config.project)
    firestore_client = firestore.Client(project=config.project)
    resolver = GcsUriResolver(storage_client)
    session = ApprovalSession.from_cloud(
        manifest=manifest,
        ledger=build_cloud_ledger(config, manifest),
        packet_writer=GcsPacketWriter(storage_client, config.packets_bucket),
        uri_resolver=resolver,
    )
    # Reads are multi-case (MOO-719: journalist cases beside the demo case); approvals
    # remain bound to the reviewed corpus case until MOO-720.
    return create_app(
        trace_reader=FirestoreTraceReader(firestore_client),
        approval=session,
        intake=IntakeGateway(
            lookup=LegistarIntakeClient(),
            store=FirestoreIntakeStore(firestore_client),
            start_creation=CreateCaseEnqueuer(config),
        ),
        bearer_token=os.environ.get("CIVICTRACE_API_BEARER"),
        uri_resolver=resolver,
    )


app = _default_app()
