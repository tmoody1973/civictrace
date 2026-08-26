"""MOO-719 create-case gates: allowlist, PDF-only, approval-required, hash-lock at fetch."""

from __future__ import annotations

import hashlib
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


def _service(
    payload: bytes = PDF_BYTES,
    convert_to_pdf=None,
    load_vaulted_pdf=None,
) -> tuple[CaseIntakeService, dict]:
    recorded: dict = {"stored": [], "manifests": []}

    def store_bytes(entry: ManifestArtifact, data: bytes) -> str:
        recorded["stored"].append((entry.local_path, len(data)))
        return f"memory://{entry.artifact_id}"

    def save_manifest(manifest: CorpusManifest) -> None:
        recorded["manifests"].append(manifest)

    service = CaseIntakeService(
        source_policy=SourcePolicy.from_yaml(ALLOWLIST),
        store_bytes=store_bytes,
        save_manifest=save_manifest,
        http_get=lambda url: payload,
        clock=lambda: NOW,
        **({"convert_to_pdf": convert_to_pdf} if convert_to_pdf else {}),
        **({"load_vaulted_pdf": load_vaulted_pdf} if load_vaulted_pdf else {}),
    )
    return service, recorded


def test_approved_bundle_becomes_a_vaulted_case_with_ordered_events() -> None:
    service, recorded = _service()
    manifest, events = service.create_case(_bundle(), _selection())
    assert manifest.case_id == "case-intake-260433"
    assert recorded["stored"] == [(manifest.artifacts[0].local_path, len(PDF_BYTES))]
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


def test_unsupported_bytes_are_refused() -> None:
    service, recorded = _service(payload=b"<html>not a public document</html>")
    with pytest.raises(CaseIntakeError, match="not a PDF or Word document"):
        service.create_case(_bundle(), _selection())
    assert recorded["manifests"] == []


def _docx_bytes() -> bytes:
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


CONVERTED = b"%PDF-1.7 converted from word"


def test_word_attachment_is_converted_and_both_copies_vaulted() -> None:
    """MOO-726: the pipeline reads the conversion; the canonical original stays vaulted."""
    docx = _docx_bytes()
    service, recorded = _service(payload=docx, convert_to_pdf=lambda data: CONVERTED)
    manifest, _ = service.create_case(_bundle(), _selection())
    entry = manifest.artifacts[0]
    assert entry.media_type == "application/pdf"
    assert entry.content_hash == "sha256:" + hashlib.sha256(CONVERTED).hexdigest()
    assert entry.original_content_hash == (
        "sha256:" + hashlib.sha256(docx).hexdigest()
    )
    assert entry.original_media_type and entry.original_media_type.endswith(
        "wordprocessingml.document"
    )
    assert entry.original_local_path and entry.original_local_path.endswith(".docx")
    assert recorded["stored"] == [
        (entry.local_path, len(CONVERTED)),
        (entry.original_local_path, len(docx)),
    ]


def test_failed_conversion_refuses_with_a_showable_reason() -> None:
    from app.services.office_convert import ConversionError

    def convert(data: bytes) -> bytes:
        raise ConversionError("the file may be damaged")

    service, recorded = _service(payload=_docx_bytes(), convert_to_pdf=convert)
    with pytest.raises(CaseIntakeError, match="damaged"):
        service.create_case(_bundle(), _selection())
    assert recorded["manifests"] == []


def test_retry_adopts_the_already_vaulted_conversion() -> None:
    """LibreOffice output varies run to run; a Cloud Tasks retry must not re-convert."""

    def never_convert(data: bytes) -> bytes:
        raise AssertionError("retry must adopt the vaulted conversion, not convert again")

    service, recorded = _service(
        payload=_docx_bytes(),
        convert_to_pdf=never_convert,
        load_vaulted_pdf=lambda object_name: CONVERTED,
    )
    manifest, _ = service.create_case(_bundle(status=BundleStatus.CREATING), _selection())
    assert manifest.artifacts[0].content_hash == (
        "sha256:" + hashlib.sha256(CONVERTED).hexdigest()
    )
