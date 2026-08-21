"""MOO-719: intake lookups, human-role manifest conversion, and the refusal paths.

Failure modes we refuse to ship: a case without a human-assigned promise document, a
selection naming attachments the record never listed, and evidence entering without a
locked hash.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from app.schemas.intake import (
    BundleStatus,
    CandidateAttachment,
    CandidateBundle,
    FetchedAttachment,
    IntakeSelection,
    build_intake_manifest,
)
from app.services.legistar_intake import IntakeLookupError, LegistarIntakeClient

NOW = datetime(2026, 8, 21, 14, 0, tzinfo=UTC)

MATTER_ROW = {
    "MatterId": 74415,
    "MatterFile": "260433",
    "MatterTitle": "Substitute resolution approving Amendment No. 1 to the Project Plan",
    "MatterName": "TID 121 amendment",
    "MatterTypeName": "Resolution",
    "MatterStatusName": "Passed",
    "MatterIntroDate": "2026-06-17T00:00:00",
}
ATTACHMENT_ROWS = [
    {
        "MatterAttachmentId": 248545,
        "MatterAttachmentName": "Amendment",
        "MatterAttachmentHyperlink": "https://milwaukee.legistar1.com/milwaukee/attachments/a.pdf",
    },
    {
        "MatterAttachmentId": 248546,
        "MatterAttachmentName": "Fiscal note",
        "MatterAttachmentHyperlink": "http://insecure.example.com/b.pdf",
    },
]


def _client(responses: dict[str, Any]) -> LegistarIntakeClient:
    def get_json(url: str) -> Any:
        for key, value in responses.items():
            if key in url:
                return value
        raise AssertionError(f"unexpected URL {url}")

    return LegistarIntakeClient(get_json=get_json)


class TestLookup:
    def test_file_number_becomes_a_candidate_bundle(self) -> None:
        client = _client({"matters?$filter": [MATTER_ROW], "attachments": ATTACHMENT_ROWS})
        bundle = client.candidate_bundle("260433", now=lambda: NOW)
        assert bundle.matter_id == 74415
        assert bundle.title.startswith("Substitute resolution")
        assert bundle.status is BundleStatus.DRAFT
        # the http:// attachment is refused as candidate evidence
        assert [a.attachment_id for a in bundle.attachments] == [248545]

    def test_unknown_file_is_a_clear_refusal(self) -> None:
        client = _client({"matters?$filter": []})
        with pytest.raises(IntakeLookupError, match="lists no matter"):
            client.candidate_bundle("999999", now=lambda: NOW)

    def test_malformed_file_number_is_refused_before_any_request(self) -> None:
        client = _client({})
        with pytest.raises(IntakeLookupError, match="six digits"):
            client.candidate_bundle("DROP TABLE", now=lambda: NOW)


def _bundle() -> CandidateBundle:
    return CandidateBundle(
        bundle_id="bundle-260433-test",
        legistar_file="260433",
        matter_id=74415,
        title="Amendment No. 1",
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


def _selection(**overrides: object) -> IntakeSelection:
    values: dict = {
        "reviewer_name": "Tarik Moody",
        "case_topic": "TID 121 commercial phase commitment and its public follow-through",
        "promise_attachment_ids": [248545],
    }
    values.update(overrides)
    return IntakeSelection.model_validate(values)


LOCKED = {
    248545: FetchedAttachment(
        attachment_id=248545, content_hash="sha256:abc", byte_length=1234, page_count=6
    )
}


class TestManifestConversion:
    def test_approved_bundle_becomes_a_manifest_equivalent_case_recipe(self) -> None:
        manifest = build_intake_manifest(_bundle(), _selection(), LOCKED, retrieved_at=NOW)
        assert manifest.case_id == "case-intake-260433"
        assert manifest.corpus_id == "intake-260433"
        entry = manifest.artifacts[0]
        assert entry.role == "original_commitment"
        assert entry.content_hash == "sha256:abc"
        assert entry.canonical_url and entry.canonical_url.startswith("https://milwaukee.legistar1.com/")
        assert manifest.duplicate_event_fixture is None
        # the recipe round-trips through the same source-event builder the pipeline uses
        event = manifest.source_event(entry.artifact_id)
        assert event.content_hash == "sha256:abc"

    def test_selection_naming_unlisted_attachment_is_refused(self) -> None:
        with pytest.raises(ValueError, match="not in the bundle"):
            build_intake_manifest(
                _bundle(), _selection(promise_attachment_ids=[999]), LOCKED, retrieved_at=NOW
            )

    def test_unfetched_attachment_cannot_enter_the_manifest(self) -> None:
        with pytest.raises(ValueError, match="not fetched and hash-locked"):
            build_intake_manifest(_bundle(), _selection(), {}, retrieved_at=NOW)

    def test_selection_requires_a_promise_document_and_a_real_topic(self) -> None:
        with pytest.raises(ValueError):
            _selection(promise_attachment_ids=[])
        with pytest.raises(ValueError):
            _selection(case_topic="short")
