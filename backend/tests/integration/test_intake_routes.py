"""MOO-719 intake endpoints: lookup, human approval, and every refusal in words."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.routes_intake import IntakeGateway
from app.core.dependencies import InMemoryTraceReader
from app.main import create_app
from app.repositories.intake import InMemoryIntakeStore
from app.schemas.intake import CandidateAttachment, CandidateBundle
from app.services.legistar_intake import IntakeLookupError

NOW = datetime(2026, 8, 21, 14, 0, tzinfo=UTC)


def _bundle() -> CandidateBundle:
    return CandidateBundle(
        bundle_id="bundle-260433-test",
        legistar_file="260433",
        matter_id=74415,
        title="Amendment No. 1 to the TID 121 Project Plan",
        matter_url="https://webapi.legistar.com/v1/milwaukee/matters/74415",
        attachments=[
            CandidateAttachment(
                attachment_id=248545,
                name="Amendment",
                url="https://milwaukee.legistar1.com/milwaukee/attachments/a.pdf",
            )
        ],
        retrieved_at=NOW,
    )


class StubLookup:
    def candidate_bundle(self, file_number: str) -> CandidateBundle:
        if file_number != "260433":
            raise IntakeLookupError("the official Legistar record lists no matter with that file")
        return _bundle()


def _client() -> tuple[TestClient, InMemoryIntakeStore, list[str]]:
    store = InMemoryIntakeStore()
    started: list[str] = []
    gateway = IntakeGateway(lookup=StubLookup(), store=store, start_creation=started.append)
    app = create_app(trace_reader=InMemoryTraceReader("case", []), intake=gateway)
    return TestClient(app), store, started


SELECTION = {
    "reviewer_name": "Tarik Moody",
    "case_topic": "TID 121 commercial phase commitment and its public follow-through",
    "promise_attachment_ids": [248545],
    "later_attachment_ids": [],
}


def test_lookup_returns_and_persists_a_draft_bundle() -> None:
    client, store, _ = _client()
    response = client.post("/intake/lookup", json={"file_number": "260433"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "DRAFT" and data["matter_id"] == 74415
    assert store.get_bundle(data["bundle_id"]) is not None


def test_unknown_file_is_a_422_in_the_officials_words() -> None:
    client, _, _ = _client()
    response = client.post("/intake/lookup", json={"file_number": "999999"})
    assert response.status_code == 422
    assert "lists no matter" in response.json()["error"]


def test_approval_marks_the_bundle_and_starts_creation_exactly_once() -> None:
    client, store, started = _client()
    lookup = client.post("/intake/lookup", json={"file_number": "260433"}).json()
    bundle_id = lookup["data"]["bundle_id"]
    response = client.post(f"/intake/bundles/{bundle_id}/approve", json=SELECTION)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "APPROVED"
    assert started == [bundle_id]
    assert store.get_selection(bundle_id) is not None
    # a second approval cannot double-create
    again = client.post(f"/intake/bundles/{bundle_id}/approve", json=SELECTION)
    assert again.status_code == 409
    assert started == [bundle_id]


def test_selection_naming_unlisted_attachments_is_refused() -> None:
    client, _, started = _client()
    lookup = client.post("/intake/lookup", json={"file_number": "260433"}).json()
    bundle_id = lookup["data"]["bundle_id"]
    bad = {**SELECTION, "promise_attachment_ids": [999]}
    response = client.post(f"/intake/bundles/{bundle_id}/approve", json=bad)
    assert response.status_code == 422
    assert "never listed" in response.json()["error"]
    assert started == []


def test_server_without_intake_says_so() -> None:
    app = create_app(trace_reader=InMemoryTraceReader("case", []))
    response = TestClient(app).post("/intake/lookup", json={"file_number": "260433"})
    assert response.status_code == 503
    assert "not enabled" in response.json()["error"]
