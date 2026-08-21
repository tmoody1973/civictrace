"""MOO-719 create-case gates: allowlist, PDF-only, approval-required, hash-lock at fetch."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.policies.source_policy import SourcePolicy
from app.schemas.corpus import CorpusManifest, ManifestArtifact
from app.schemas.intake import (
    BundleStatus,
    CandidateAttachment,
    CandidateBundle,
    IntakeSelection,
)
from app.services.case_intake import CaseIntakeError, CaseIntakeService
from tests.conftest import REPO_ROOT

NOW = datetime(2026, 8, 21, 14, 0, tzinfo=UTC)
ALLOWLIST = REPO_ROOT / "docs" / "sources" / "source-allowlist.yaml"
PDF_BYTES = b"%PDF-1.4 minimal test payload"


def _bundle(
    status: BundleStatus = BundleStatus.APPROVED, url: str | None = None
) -> CandidateBundle:
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
                url=url or "https://milwaukee.legistar1.com/milwaukee/attachments/a.pdf",
            )
        ],
        retrieved_at=NOW,
        status=status,
    )


def _selection() -> IntakeSelection:
    return IntakeSelection(
        reviewer_name="Tarik Moody",
        case_topic="TID 121 commercial phase commitment and its public follow-through",
        promise_attachment_ids=[248545],
    )


def _service(payload: bytes = PDF_BYTES) -> tuple[CaseIntakeService, dict]:
    recorded: dict = {"stored": [], "manifests": []}

    def store_bytes(entry: ManifestArtifact, data: bytes) -> str:
        recorded["stored"].append((entry.artifact_id, len(data)))
        return f"memory://{entry.artifact_id}"

    def save_manifest(manifest: CorpusManifest) -> None:
        recorded["manifests"].append(manifest)

    service = CaseIntakeService(
        source_policy=SourcePolicy.from_yaml(ALLOWLIST),
        store_bytes=store_bytes,
        save_manifest=save_manifest,
        http_get=lambda url: payload,
        clock=lambda: NOW,
    )
    return service, recorded


def test_approved_bundle_becomes_a_vaulted_case_with_ordered_events() -> None:
    service, recorded = _service()
    manifest, events = service.create_case(_bundle(), _selection())
    assert manifest.case_id == "case-intake-260433"
    assert recorded["stored"] == [(manifest.artifacts[0].artifact_id, len(PDF_BYTES))]
    assert recorded["manifests"] == [manifest]
    assert [event.artifact_id for event in events] == [manifest.artifacts[0].artifact_id]
    locked_hash = manifest.artifacts[0].content_hash
    assert locked_hash and locked_hash.startswith("sha256:")


def test_unapproved_bundle_is_refused_before_any_fetch() -> None:
    service, recorded = _service()
    with pytest.raises(CaseIntakeError, match="only an approved"):
        service.create_case(_bundle(status=BundleStatus.DRAFT), _selection())
    assert recorded["stored"] == [] and recorded["manifests"] == []


def test_already_created_bundle_is_refused() -> None:
    service, recorded = _service()
    with pytest.raises(CaseIntakeError, match="only an approved"):
        service.create_case(_bundle(status=BundleStatus.CASE_CREATED), _selection())
    assert recorded["manifests"] == []


def test_creating_status_is_a_legitimate_retry_not_a_refusal() -> None:
    """A cloud-task retry after a crash sees CREATING; it must not be told 'unapproved'."""
    service, recorded = _service()
    manifest, _ = service.create_case(_bundle(status=BundleStatus.CREATING), _selection())
    assert recorded["manifests"] == [manifest]


def test_off_allowlist_url_is_refused() -> None:
    service, recorded = _service()
    bundle = _bundle(url="https://evil.example.com/looks-official.pdf")
    with pytest.raises(CaseIntakeError, match="evil.example.com"):
        service.create_case(bundle, _selection())
    assert recorded["manifests"] == []


def test_non_pdf_bytes_are_refused() -> None:
    service, recorded = _service(payload=b"<html>not a public document</html>")
    with pytest.raises(CaseIntakeError, match="not a PDF document"):
        service.create_case(_bundle(), _selection())
    assert recorded["manifests"] == []
