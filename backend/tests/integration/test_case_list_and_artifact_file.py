"""MOO-696: the Evidence Studio can list cases and fetch the exact vaulted PDF bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import InMemoryTraceReader, JsonLedgerReader
from app.main import create_app
from tests.conftest import CASE_ID

FRONTEND_ORIGIN = "http://localhost:3000"


@pytest.fixture(scope="module")
def client(ledger_json: tuple[Path, list]) -> TestClient:
    return TestClient(create_app(trace_reader=JsonLedgerReader(ledger_json[0])))


@pytest.fixture(scope="module")
def stored_artifacts(ledger_json: tuple[Path, list]) -> list[dict]:
    events = json.loads(ledger_json[0].read_text())["events"]
    return [event["artifact"] for event in events if event["event_type"] == "ARTIFACT_STORED"]


def test_case_list_returns_summaries(client: TestClient) -> None:
    body = client.get("/cases").json()
    assert body["ok"] is True and body["error"] is None
    assert [case["case_id"] for case in body["data"]] == [CASE_ID]
    assert body["data"][0]["state"] == "DELTA_STAGED"


def test_case_list_empty_ledger_is_empty_list() -> None:
    empty = TestClient(create_app(trace_reader=InMemoryTraceReader("x", [])))
    body = empty.get("/cases").json()
    assert body == {"ok": True, "data": [], "error": None}


def test_artifact_file_serves_exact_bytes_with_hash_headers(
    client: TestClient, stored_artifacts: list[dict]
) -> None:
    artifact = stored_artifacts[0]
    response = client.get(f"/artifacts/{artifact['artifact_id']}/file")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(artifact["media_type"])
    digest = "sha256:" + hashlib.sha256(response.content).hexdigest()
    assert digest == artifact["content_hash"]
    assert response.headers["x-civictrace-content-hash"] == artifact["content_hash"]
    assert response.headers["etag"] == f'"{artifact["content_hash"]}"'
    assert response.headers["cache-control"] == "private, max-age=0"


def test_head_returns_headers_without_body(
    client: TestClient, stored_artifacts: list[dict]
) -> None:
    artifact = stored_artifacts[0]
    response = client.head(f"/artifacts/{artifact['artifact_id']}/file")
    assert response.status_code == 200
    assert response.headers["x-civictrace-content-hash"] == artifact["content_hash"]
    assert response.content == b""


def test_every_stored_document_is_servable_and_media_is_refused_inline(
    client: TestClient, stored_artifacts: list[dict]
) -> None:
    assert len(stored_artifacts) >= 4
    for artifact in stored_artifacts:
        response = client.get(f"/artifacts/{artifact['artifact_id']}/file")
        if (artifact.get("media_type") or "").startswith(("video/", "audio/")):
            # A 2.9GB recording must never be read into API memory; the reviewer
            # reaches it through transcript evidence and the official source link.
            assert response.status_code == 413
            assert "not served inline" in response.json()["error"]
        else:
            assert response.status_code == 200


def test_unknown_artifact_is_404_envelope(client: TestClient) -> None:
    response = client.get("/artifacts/nope/file")
    assert response.status_code == 404
    assert response.json() == {"ok": False, "data": None, "error": "artifact 'nope' not found"}


def test_not_published_artifact_is_404_with_reason(client: TestClient) -> None:
    trace = client.get(f"/cases/{CASE_ID}/trace").json()["data"]["events"]
    missing = next(row for row in trace if row["event_type"] == "ARTIFACT_NOT_PUBLISHED")
    response = client.get(f"/artifacts/{missing['artifact_id']}/file")
    assert response.status_code == 404
    assert response.json()["ok"] is False
    assert "NOT_PUBLISHED" in response.json()["error"]


def test_path_traversal_in_id_is_just_not_found(client: TestClient) -> None:
    response = client.get("/artifacts/..%2F..%2Fetc%2Fpasswd/file")
    assert response.status_code == 404
    assert response.json()["ok"] is False


def test_cors_allows_frontend_origin(client: TestClient) -> None:
    response = client.options(
        "/cases",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == FRONTEND_ORIGIN
