"""First write endpoints: staged inquiry → approve/reject → packet. Fail closed, envelope always."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.approval_session import ApprovalSession
from app.services.replay import ReplayOptions
from tests.conftest import ALLOWLIST_PATH, FIXTURE_DIR, MANIFEST_PATH, REPO_ROOT

NOW = datetime(2026, 8, 19, 18, 0, tzinfo=UTC)
CASE_ID = "case-tid121-bronzeville-arts-tech-hub"
REVIEWER = "Tarik Moody"


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    session = ApprovalSession.from_replay(
        ReplayOptions(
            manifest_path=MANIFEST_PATH,
            allowlist_path=ALLOWLIST_PATH,
            extraction_path=FIXTURE_DIR / "fixture_extraction.json",
            fixture_root=REPO_ROOT,
            vault_dir=tmp_path / "vault",
        ),
        packet_dir=tmp_path / "packets",
        clock=lambda: NOW,
    )
    return TestClient(create_app(trace_reader=session, approval=session))


def _staged_hash(client: TestClient) -> str:
    body = client.get(f"/cases/{CASE_ID}/inquiry").json()
    assert body["ok"], body
    return str(body["data"]["artifact_hash"])


def test_get_staged_inquiry_with_hash(client: TestClient) -> None:
    response = client.get(f"/cases/{CASE_ID}/inquiry")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "2025 Annual Report" in data["proposal"]["proposed_question"]
    assert data["artifact_hash"].startswith("sha256:")
    assert data["ttl_minutes"] == 30


def test_get_inquiry_unknown_case_is_404_envelope(client: TestClient) -> None:
    response = client.get("/cases/nope/inquiry")
    assert response.status_code == 404
    body = response.json()
    assert body["ok"] is False and "not found" in body["error"]


def test_packet_before_approval_is_404_envelope(client: TestClient) -> None:
    response = client.get(f"/cases/{CASE_ID}/packet")
    assert response.status_code == 404
    body = response.json()
    assert body["ok"] is False and "no packet" in body["error"]


def test_approve_renders_packet_and_get_packet_returns_it(client: TestClient) -> None:
    staged_hash = _staged_hash(client)
    response = client.post(
        f"/cases/{CASE_ID}/inquiry/approve",
        json={"reviewer_name": REVIEWER, "artifact_hash": staged_hash},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["packet_hash"].startswith("sha256:")
    assert data["token_id"].startswith("tok_")
    assert data["expires_at"]

    packet = client.get(f"/cases/{CASE_ID}/packet")
    assert packet.status_code == 200
    packet_data = packet.json()["data"]
    assert packet_data["packet_hash"] == data["packet_hash"]
    assert packet_data["markdown"].startswith("# DRAFT")
    assert "not sent; no external action taken" in packet_data["markdown"]

    trace = client.get(f"/cases/{CASE_ID}/trace").json()["data"]
    kinds = [event["event_type"] for event in trace["events"]]
    assert "INQUIRY_APPROVAL_ISSUED" in kinds and "PACKET_RENDERED" in kinds


def test_hash_echo_mismatch_is_409_and_renders_nothing(client: TestClient) -> None:
    response = client.post(
        f"/cases/{CASE_ID}/inquiry/approve",
        json={"reviewer_name": REVIEWER, "artifact_hash": "sha256:" + "0" * 64},
    )
    assert response.status_code == 409
    body = response.json()
    assert body["ok"] is False
    assert "you approved different bytes than are staged" in body["error"]

    assert client.get(f"/cases/{CASE_ID}/packet").status_code == 404
    trace = client.get(f"/cases/{CASE_ID}/trace").json()["data"]
    kinds = [event["event_type"] for event in trace["events"]]
    assert "APPROVAL_REFUSED" in kinds and "PACKET_RENDERED" not in kinds


def test_missing_reviewer_name_is_422(client: TestClient) -> None:
    staged_hash = _staged_hash(client)
    response = client.post(
        f"/cases/{CASE_ID}/inquiry/approve",
        json={"reviewer_name": "  ", "artifact_hash": staged_hash},
    )
    assert response.status_code == 422


def test_reject_writes_ledger_row(client: TestClient) -> None:
    response = client.post(
        f"/cases/{CASE_ID}/inquiry/reject",
        json={"reviewer_name": REVIEWER, "note": "Question scope is wider than the staged delta."},
    )
    assert response.status_code == 200
    trace = client.get(f"/cases/{CASE_ID}/trace").json()["data"]
    rejected = [
        event
        for event in trace["events"]
        if event["event_type"] == "INQUIRY_APPROVAL_REJECTED"
    ]
    assert len(rejected) == 1
    assert "Question scope" in (rejected[0]["reason"] or "")


def test_static_reader_without_approval_gateway_is_503(tmp_path: Path, client: TestClient) -> None:
    """A server built on a static ledger.json cannot approve; it must say so, not crash."""
    from app.core.dependencies import InMemoryTraceReader

    static_app = create_app(trace_reader=InMemoryTraceReader(CASE_ID, []))
    static_client = TestClient(static_app)
    response = static_client.post(
        f"/cases/{CASE_ID}/inquiry/approve",
        json={"reviewer_name": REVIEWER, "artifact_hash": "sha256:" + "0" * 64},
    )
    assert response.status_code == 503
    assert "live" in response.json()["error"]
