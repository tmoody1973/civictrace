"""Bearer gate, worker endpoints, URI resolver, and GCS packet writer — all offline."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.dependencies import InMemoryTraceReader
from app.domain.enums import JobStatus
from app.main import create_app
from app.orchestration.workflow import WorkflowResult
from app.schemas.source import SourceEvent
from app.services.packet_store import GcsPacketWriter
from app.services.uri_bytes import GcsUriResolver
from app.worker import create_worker_app
from tests.unit.test_gcs_artifact_vault import FakeStorageClient

CASE_ID = "case-tid121-bronzeville-arts-tech-hub"

EVENT = SourceEvent(
    source_event_id="se-1",
    source_id="milwaukee-legistar",
    jurisdiction="milwaukee",
    artifact_id="tid121-project-plan-2024",
    external_id="240382",
    canonical_url="https://milwaukee.legistar1.com/x.pdf",
    observed_at=datetime(2026, 8, 19, tzinfo=UTC),
)


# --- bearer gate -----------------------------------------------------------------


def _bearer_client() -> TestClient:
    return TestClient(
        create_app(trace_reader=InMemoryTraceReader(CASE_ID, []), bearer_token="right-token")
    )


def test_missing_bearer_is_401_in_words() -> None:
    response = _bearer_client().get("/cases")
    assert response.status_code == 401
    assert response.json()["error"] == "missing or wrong bearer token"


def test_wrong_bearer_is_401() -> None:
    response = _bearer_client().get("/cases", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_right_bearer_passes() -> None:
    response = _bearer_client().get(
        "/cases", headers={"Authorization": "Bearer right-token"}
    )
    assert response.status_code == 200


def test_healthz_needs_no_bearer() -> None:
    assert _bearer_client().get("/healthz").status_code == 200


def test_no_bearer_configured_stays_open() -> None:
    client = TestClient(create_app(trace_reader=InMemoryTraceReader(CASE_ID, [])))
    assert client.get("/cases").status_code == 200


# --- worker app ------------------------------------------------------------------


class FakeIngestor:
    def __init__(self) -> None:
        self.events: list[SourceEvent] = []

    async def run(self, event: SourceEvent, *, trace_id: str) -> WorkflowResult:
        self.events.append(event)
        return WorkflowResult(status=JobStatus.SUCCEEDED, job_key="job-1")


class FakeEnqueuer:
    def __init__(self) -> None:
        self.events: list[SourceEvent] = []

    def enqueue(self, event: SourceEvent) -> str:
        self.events.append(event)
        return "task-1"


def _worker() -> tuple[TestClient, FakeIngestor, FakeEnqueuer]:
    ingestor, enqueuer = FakeIngestor(), FakeEnqueuer()
    return TestClient(create_worker_app(ingestor=ingestor, enqueuer=enqueuer)), ingestor, enqueuer


def test_pubsub_push_enqueues_exactly_one_task() -> None:
    client, ingestor, enqueuer = _worker()
    envelope = {
        "message": {"data": base64.b64encode(EVENT.model_dump_json().encode()).decode()}
    }
    response = client.post("/pubsub/source-events", json=envelope)
    assert response.status_code == 200 and response.json()["ok"] is True
    assert [e.artifact_id for e in enqueuer.events] == ["tid121-project-plan-2024"]
    assert ingestor.events == []  # nothing heavy inside event delivery


def test_pubsub_poison_message_is_acked_not_retried() -> None:
    client, _, enqueuer = _worker()
    envelope = {"message": {"data": base64.b64encode(b"not json").decode()}}
    response = client.post("/pubsub/source-events", json=envelope)
    assert response.status_code == 200 and response.json()["ok"] is False
    assert enqueuer.events == []


def test_task_ingest_runs_the_workflow() -> None:
    client, ingestor, _ = _worker()
    response = client.post(
        "/tasks/ingest-source-event", json=json.loads(EVENT.model_dump_json())
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "SUCCEEDED"
    assert [e.artifact_id for e in ingestor.events] == ["tid121-project-plan-2024"]


def test_task_malformed_payload_refused_without_retry() -> None:
    client, ingestor, _ = _worker()
    response = client.post("/tasks/ingest-source-event", json={"nope": True})
    assert response.status_code == 200 and response.json()["ok"] is False
    assert ingestor.events == []


# --- URI resolver + packet writer ------------------------------------------------


def test_gcs_resolver_downloads_once_and_caches(tmp_path: Path) -> None:
    client = FakeStorageClient()
    bucket = client.bucket("b")
    blob = bucket.blob("doc.pdf")
    blob.metadata = {}
    blob.upload_from_string(b"payload", if_generation_match=0)
    resolver = GcsUriResolver(client, cache_dir=tmp_path)  # type: ignore[arg-type]
    first = resolver.to_local_path("gs://b/doc.pdf")
    assert first.read_bytes() == b"payload"
    bucket.objects["doc.pdf"] = b"changed-upstream"
    assert resolver.read_bytes("gs://b/doc.pdf") == b"payload"  # cached copy wins


def test_gcs_packet_writer_is_idempotent() -> None:
    client = FakeStorageClient()
    writer = GcsPacketWriter(client, "packets")  # type: ignore[arg-type]
    first = writer.write("packet.md", "# DRAFT")
    second = writer.write("packet.md", "# DRAFT")
    assert first == second == "gs://packets/packet.md"
    assert client.buckets["packets"].objects["packet.md"] == b"# DRAFT"
