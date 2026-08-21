"""CivicTrace worker service (Slice 5.3, MOO-709). IAM-only on Cloud Run.

Two entrances, both narrow:
- POST /pubsub/source-events: Pub/Sub push → validate → enqueue one Cloud Task.
  Nothing heavy happens here (gcp-operations rule: no ingestion inside event delivery).
- POST /tasks/ingest-source-event: Cloud Tasks target → run ONE source event through the
  deterministic workflow. Retries are no-ops via job + ledger idempotency.

Run: CIVICTRACE_WORKER=1 GOOGLE_CLOUD_PROJECT=... uvicorn app.worker:app
"""

from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any, Protocol

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.orchestration.workflow import WorkflowResult
from app.schemas.api import ApiEnvelope, HealthResponse
from app.schemas.source import SourceEvent

logger = logging.getLogger("civictrace.worker")


class SourceEventIngestor(Protocol):
    async def run(self, event: SourceEvent, *, trace_id: str) -> WorkflowResult: ...


class CorpusPrefilter(Protocol):
    def manifest_row(self, artifact_id: str) -> object | None: ...


class TaskEnqueuer(Protocol):
    def enqueue(self, event: SourceEvent, *, message_id: str | None = None) -> str:
        """Create (or dedupe) the ingest task; returns the task name."""
        ...


class CaseCreator(Protocol):
    async def run(self, bundle_id: str) -> dict[str, str]: ...


def create_worker_app(
    *,
    ingestor: SourceEventIngestor,
    enqueuer: TaskEnqueuer,
    case_creator: CaseCreator | None = None,
) -> FastAPI:
    app = FastAPI(title="CivicTrace worker", version="0.1.0")

    @app.get("/healthz", response_model=ApiEnvelope[HealthResponse])
    def healthz() -> ApiEnvelope[HealthResponse]:
        return ApiEnvelope(ok=True, data=HealthResponse(status="ok"), error=None)

    @app.post("/pubsub/source-events")
    async def pubsub_push(request: Request) -> JSONResponse:
        """Acknowledge malformed messages (200) so a poison message cannot retry forever;
        the refusal is logged. Well-formed messages become exactly one named task."""
        try:
            envelope = await request.json()
            payload = json.loads(base64.b64decode(envelope["message"]["data"]))
            event = SourceEvent.model_validate(payload)
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            logger.error("pubsub message refused: %s", exc)
            return _json(200, ok=False, error=f"message refused: {type(exc).__name__}")
        task_name = enqueuer.enqueue(event, message_id=envelope["message"].get("messageId"))
        return _json(200, ok=True, data={"task": task_name})

    @app.post("/tasks/ingest-source-event")
    async def ingest(request: Request) -> JSONResponse:
        try:
            event = SourceEvent.model_validate(await request.json())
        except (ValueError, ValidationError) as exc:
            # A malformed task will never become well-formed; do not let Tasks retry it.
            logger.error("task payload refused: %s", exc)
            return _json(200, ok=False, error=f"payload refused: {type(exc).__name__}")
        trace_id = request.headers.get("X-CloudTasks-TaskName", "task")
        result = await ingestor.run(event, trace_id=trace_id)
        return _json(
            200,
            ok=True,
            data={"status": result.status, "job_key": result.job_key, "reason": result.reason},
        )

    @app.post("/tasks/create-case")
    async def create_case(request: Request) -> JSONResponse:
        """Case intake (MOO-719): one task runs the full gated chain from durable state.

        Deterministic refusals return 200 (retrying cannot fix them; the bundle records
        the reason). Unexpected errors raise → 500 → bounded Cloud Tasks retries."""
        if case_creator is None:
            return _json(200, ok=False, error="case intake is not enabled on this worker")
        try:
            payload = await request.json()
            bundle_id = str(payload["bundle_id"])
        except (KeyError, TypeError, ValueError) as exc:
            logger.error("create-case payload refused: %s", exc)
            return _json(200, ok=False, error=f"payload refused: {type(exc).__name__}")
        result = await case_creator.run(bundle_id)
        return _json(200, ok=result.get("status") == "CASE_CREATED", data=result)

    return app


def _json(
    status_code: int, *, ok: bool, data: Any = None, error: str | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"ok": ok, "data": data, "error": error}
    )


class WorkflowIngestor:
    """Builds the cloud workflow once and runs one event at a time through it.

    With CIVICTRACE_BQ_PREFILTER=1 each event must have a manifest row in BigQuery
    (the bounded-evidence prefilter, MOO-710); a missing row fails closed. A BigQuery
    outage raises → 500 → Cloud Tasks retries within the queue's bounded retry caps.
    """

    def __init__(
        self,
        *,
        workflow: SourceEventIngestor | None = None,
        prefilter: CorpusPrefilter | None = None,
    ) -> None:
        usage_log = None
        if workflow is None:
            from app.services.cloud import (
                CloudConfig,
                build_cloud_workflow,
                build_corpus_prefilter,
            )

            config = CloudConfig.from_env()
            prefilter = build_corpus_prefilter(config)
            workflow, _, _, usage_log = build_cloud_workflow(config, prefilter=prefilter)
        self._workflow = workflow
        self._prefilter = prefilter
        self._usage_log = usage_log
        self._usage_seen = 0

    async def run(self, event: SourceEvent, *, trace_id: str) -> WorkflowResult:
        if self._prefilter is not None and self._prefilter.manifest_row(event.artifact_id) is None:
            from app.domain.enums import JobStatus

            logger.error(
                "%s: artifact %s has no corpus_artifacts row; event refused",
                trace_id,
                event.artifact_id,
            )
            return WorkflowResult(
                status=JobStatus.FAILED,
                job_key=f"prefilter:{event.artifact_id}",
                reason="artifact not in the reviewed corpus (BigQuery prefilter)",
            )
        try:
            return await self._workflow.run(event, trace_id=trace_id)
        finally:
            self._log_model_usage()

    def _log_model_usage(self) -> None:
        """One structured Cloud Logging line per model call: tokens, latency, estimated USD."""
        if self._usage_log is None:
            return
        from dataclasses import asdict

        for record in self._usage_log.records[self._usage_seen :]:
            logger.info(
                "model_usage %s",
                json.dumps({**asdict(record), "estimated_usd": round(record.estimated_usd(), 6)}),
            )
        self._usage_seen = len(self._usage_log.records)


class CloudTasksEnqueuer:
    """Creates one named task per source version; Tasks dedupes by name, the workflow by job key."""

    def __init__(self) -> None:
        from google.cloud import tasks_v2

        from app.services.cloud import CloudConfig

        config = CloudConfig.from_env()
        self._client = tasks_v2.CloudTasksClient()
        self._queue_path = self._client.queue_path(
            config.project, config.region, config.tasks_queue
        )
        self._worker_url = config.worker_url.rstrip("/")
        self._invoker_email = os.environ.get("CIVICTRACE_WORKER_SA", "")

    def enqueue(self, event: SourceEvent, *, message_id: str | None = None) -> str:
        from google.api_core.exceptions import AlreadyExists
        from google.cloud import tasks_v2

        from app.orchestration.idempotency import SourceJobKeys
        from app.orchestration.workflow import CityDocumentWorkflow

        job_key = SourceJobKeys().source_job_key(
            event, workflow_version=CityDocumentWorkflow.WORKFLOW_VERSION
        )
        task_id = job_key.replace(":", "-").replace("/", "-")
        if message_id:
            # Duplicate suppression is the persisted job repo's responsibility (MOO-710);
            # a per-message task name keeps replays repeatable (Tasks burns names for ~1h).
            task_id = f"{task_id}-{message_id}"
        task_name = f"{self._queue_path}/tasks/{task_id}"
        task = tasks_v2.Task(
            name=task_name,
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=f"{self._worker_url}/tasks/ingest-source-event",
                headers={"Content-Type": "application/json"},
                body=event.model_dump_json().encode("utf-8"),
                oidc_token=tasks_v2.OidcToken(service_account_email=self._invoker_email),
            ),
        )
        try:
            self._client.create_task(parent=self._queue_path, task=task)
        except AlreadyExists:
            logger.info("task %s already queued; duplicate delivery suppressed", task_id)
        return task_id


def _default_app() -> FastAPI | None:
    """Uvicorn entry point for Cloud Run; tests build their own app via create_worker_app()."""
    if not os.environ.get("CIVICTRACE_WORKER"):
        return None
    # Python's default level drops INFO: model_usage and duplicate-suppression lines
    # must reach Cloud Logging, so the worker opts in explicitly.
    logging.basicConfig(level=logging.INFO)
    from app.services.cloud_intake import CloudCaseCreator

    return create_worker_app(
        ingestor=WorkflowIngestor(),
        enqueuer=CloudTasksEnqueuer(),
        case_creator=CloudCaseCreator(),
    )


app = _default_app()
