"""One command runs the corpus; one URL shows the Evidence Trace. All four states visible."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import JsonLedgerReader
from app.domain.enums import JobStatus
from app.main import create_app
from tests.conftest import MANIFEST_PATH

CASE_ID = "case-tid121-bronzeville-arts-tech-hub"
NOW = datetime(2026, 8, 19, 16, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def client(ledger_json: tuple[Path, list]) -> TestClient:
    return TestClient(create_app(trace_reader=JsonLedgerReader(ledger_json[0])))


def test_replay_results_show_every_state(ledger_json: tuple[Path, list]) -> None:
    statuses = [result.status for result in ledger_json[1]]
    assert statuses.count(JobStatus.SUCCEEDED) == 4  # 3 documents + the meeting recording
    assert statuses.count(JobStatus.NOT_PUBLISHED) == 1
    assert statuses.count(JobStatus.DUPLICATE_SUPPRESSED) == 1
    assert JobStatus.EXTRACTION_REJECTED not in statuses


def test_ledger_json_is_written_and_typed(ledger_json: tuple[Path, list]) -> None:
    payload = json.loads(ledger_json[0].read_text())
    assert payload["case_id"] == CASE_ID
    assert {event["event_type"] for event in payload["events"]} >= {
        "ARTIFACT_STORED",
        "EVIDENCE_ACCEPTED",
        "ARTIFACT_NOT_PUBLISHED",
    }


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "data": {"status": "ok"}, "error": None}


def test_trace_shows_anchored_evidence_and_not_published(client: TestClient) -> None:
    response = client.get(f"/cases/{CASE_ID}/trace")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True and body["error"] is None
    data = body["data"]
    assert data["case_id"] == CASE_ID
    events = data["events"]

    accepted = [event for event in events if event["event_type"] == "EVIDENCE_ACCEPTED"]
    assert len(accepted) == 11  # 8 document + 3 meeting-transcript evidence objects
    assert all(event["anchors"] for event in accepted), "every evidence event has >= 1 anchor"
    assert all(
        event["canonical_url"].startswith(
            ("https://milwaukee.legistar1.com/", "https://milwaukee.granicus.com/")
        )
        for event in accepted
    )
    assert all(event["verbatim_excerpt"] and event["neutral_statement"] for event in accepted)
    pages = {
        (event["artifact_id"], anchor["anchor_value"])
        for event in accepted
        for anchor in event["anchors"]
    }
    assert ("tid121-project-plan-2024", "5") in pages  # manifest required_anchors
    assert ("tid121-amendment-1-2026", "3") in pages
    assert ("znd-committee-2026-07-28", "693120-696360") in pages  # committee action moment

    missing = [event for event in events if event["event_type"] == "ARTIFACT_NOT_PUBLISHED"]
    assert len(missing) == 1
    assert missing[0]["status"] == "NOT_PUBLISHED"
    assert missing[0]["artifact_id"] == "tid-annual-report-2025"
    assert missing[0]["reason"] and "2026-08-19" in missing[0]["reason"]

    stored = [event for event in events if event["event_type"] == "ARTIFACT_STORED"]
    assert len(stored) == 4 and all(event["content_hash"].startswith("sha256:") for event in stored)

    assert len({event["event_id"] for event in events}) == len(events), (
        "duplicate run added nothing"
    )


def test_trace_has_no_free_text_summary_fields(client: TestClient) -> None:
    event = client.get(f"/cases/{CASE_ID}/trace").json()["data"]["events"][0]
    assert not {"summary", "narrative", "reasoning"} & set(event)


def test_unknown_case_is_404_envelope(client: TestClient) -> None:
    response = client.get("/cases/nope/trace")
    assert response.status_code == 404
    assert response.json() == {"ok": False, "data": None, "error": "case 'nope' not found"}


def test_cli_main_exit_code_and_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import replay_corpus as cli  # noqa: PLC0415

    code = cli.main(
        [
            str(MANIFEST_PATH),
            "--replay-duplicate",
            "--out",
            str(tmp_path / "ledger.json"),
            "--vault-dir",
            str(tmp_path / "vault"),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "DUPLICATE_SUPPRESSED" in out and "NOT_PUBLISHED" in out and "SUCCEEDED" in out


def test_trace_shows_delta_and_review_rows(client: TestClient) -> None:
    events = client.get(f"/cases/{CASE_ID}/trace").json()["data"]["events"]
    staged = [e for e in events if e["event_type"] == "DELTA_STAGED"]
    assert len(staged) == 2  # the amendment revision, then the hearing-citing advance
    hearing = staged[1]
    assert hearing["category"] == "ADVANCED"
    assert set(hearing["later_evidence_ids"]) == {
        "ev-znd-tid121-amendment-purpose",
        "ev-znd-tid121-developer-timeline",
        "ev-znd-tid121-committee-action",
    }
    row = staged[0]
    assert row["status"] == "DELTA_STAGED"
    assert row["category"] == "REVISED"
    assert "$700,000" in row["neutral_summary"] and "$2,345,000" in row["neutral_summary"]
    assert row["original_evidence_ids"] == ["ev-tid121-plan-capital-costs"]
    assert set(row["later_evidence_ids"]) == {
        "ev-tid121-amend1-capital-costs",
        "ev-tid121-amend1-commercial-grant",
    }
    assert row["what_is_established"] and row["what_is_not_established"]
    assert "2025 Annual Report" in row["next_evidence_needed"]
    assert row["requires_human_review"] is True
    assert (
        row["review_outcome"] == "APPROVE" and row["blocking_issues"] == [] and row["review_notes"]
    )
    # both anchor sides resolve to earlier EVIDENCE_ACCEPTED rows in the same response
    accepted_ids = {e["evidence_id"] for e in events if e["event_type"] == "EVIDENCE_ACCEPTED"}
    assert set(row["original_evidence_ids"]) <= accepted_ids
    assert set(row["later_evidence_ids"]) <= accepted_ids
    kinds = [e["event_type"] for e in events]
    assert kinds.index("DELTA_PROPOSED") < kinds.index("DELTA_STAGED")
    no_material = [e for e in events if e["event_type"] == "NO_MATERIAL_DELTA"]
    assert len(no_material) == 2 and all(e["reason"] for e in no_material)


def test_case_summary_endpoint(client: TestClient) -> None:
    response = client.get(f"/cases/{CASE_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["case_id"] == CASE_ID
    assert "Tax Incremental District No. 121" in data["case_topic"]
    assert data["state"] == "DELTA_STAGED"
    assert data["counts"] == {
        "artifacts_stored": 4,
        "evidence_accepted": 11,
        "not_published": 1,
        "extractions_rejected": 0,
        "deltas_proposed": 2,
        "deltas_rejected": 0,
    }
    latest = data["latest_delta"]
    assert latest["category"] == "ADVANCED" and latest["review_outcome"] == "APPROVE"
    assert latest["requires_human_review"] is True
    assert "Common Council action record" in data["next_evidence_needed"]
    assert not {"summary", "narrative", "reasoning"} & set(data)


def test_case_summary_unknown_is_404_envelope(client: TestClient) -> None:
    response = client.get("/cases/nope")
    assert response.status_code == 404
    assert response.json() == {"ok": False, "data": None, "error": "case 'nope' not found"}


def test_cli_prints_case_outcome_line(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import replay_corpus as cli  # noqa: PLC0415

    cli.main([str(MANIFEST_PATH), "--vault-dir", str(tmp_path / "vault")])
    out = capsys.readouterr().out
    assert (
        "DELTA_STAGED (ADVANCED)" in out
        and "reviewer=APPROVE" in out
        and "Common Council action record" in out
    )
