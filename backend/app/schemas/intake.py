"""Journalist case intake (Slice 7.1, MOO-719). Pure: pydantic + stdlib.

A CandidateBundle is what the Legistar Web API said about one matter — it is NOT a case.
Only an explicit human approval, with roles assigned and a topic stated, may turn it into
a manifest-equivalent case recipe. First canonical retrieval sets the hash-lock: the human
reviews the official listing; the system locks the exact bytes at approval time.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ArtifactAvailability
from app.schemas.corpus import CorpusManifest, ManifestArtifact

INTAKE_SOURCE_ID = "milwaukee_legistar"
INTAKE_JURISDICTION = "milwaukee_city"


class BundleStatus(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    CREATING = "CREATING"
    CASE_CREATED = "CASE_CREATED"
    FAILED = "FAILED"


class MatterSearchResult(BaseModel):
    """One row from a plain-words search of the official record (MOO-749).

    Everything here is verbatim Legistar data; the file number is the OUTPUT the
    journalist clicks, never the knowledge they must arrive with.
    """

    model_config = ConfigDict(extra="forbid")

    legistar_file: str
    matter_id: int
    title: str
    matter_type: str | None = None
    matter_status: str | None = None
    intro_date: date | None = None


class CandidateAttachment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attachment_id: int
    name: str
    url: str


class CandidateBundle(BaseModel):
    """What the official record lists for one Legistar file. No conclusions, no case."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    legistar_file: str
    matter_id: int
    title: str
    matter_type: str | None = None
    matter_status: str | None = None
    intro_date: date | None = None
    matter_url: str
    attachments: list[CandidateAttachment] = Field(default_factory=list)
    retrieved_at: datetime
    status: BundleStatus = BundleStatus.DRAFT
    failure_reason: str | None = None
    case_id: str | None = None


class IntakeSelection(BaseModel):
    """The human's review: which attachment is the promise, what the case is about."""

    model_config = ConfigDict(extra="forbid")

    reviewer_name: str = Field(min_length=1)
    case_topic: str = Field(min_length=10)
    promise_attachment_ids: list[int] = Field(min_length=1)
    later_attachment_ids: list[int] = Field(default_factory=list)


class FetchedAttachment(BaseModel):
    """One attachment after canonical retrieval: the bytes are hashed and vaulted."""

    model_config = ConfigDict(extra="forbid")

    attachment_id: int
    content_hash: str
    byte_length: int
    page_count: int | None = None


def intake_corpus_id(legistar_file: str) -> str:
    return f"intake-{legistar_file}"


def intake_case_id(legistar_file: str) -> str:
    return f"case-intake-{legistar_file}"


def build_intake_manifest(
    bundle: CandidateBundle,
    selection: IntakeSelection,
    fetched: dict[int, FetchedAttachment],
    *,
    retrieved_at: datetime,
) -> CorpusManifest:
    """Deterministic conversion: approved bundle + human roles + locked hashes → case recipe.

    The result is the SAME shape as the reviewed corpus manifest, so every downstream seam
    (vault, agents, validators, ledger) treats a journalist case exactly like the demo case.
    """
    selected = {
        **{aid: "original_commitment" for aid in selection.promise_attachment_ids},
        **{aid: "later_evidence" for aid in selection.later_attachment_ids},
    }
    by_id = {attachment.attachment_id: attachment for attachment in bundle.attachments}
    unknown = sorted(set(selected) - set(by_id))
    if unknown:
        raise ValueError(f"selection names attachments not in the bundle: {unknown}")
    missing = sorted(set(selected) - set(fetched))
    if missing:
        raise ValueError(f"attachments not fetched and hash-locked yet: {missing}")
    artifacts = [
        _manifest_artifact(
            bundle, by_id[attachment_id], role, fetched[attachment_id], retrieved_at
        )
        for attachment_id, role in selected.items()
    ]
    return CorpusManifest(
        version=1,
        corpus_id=intake_corpus_id(bundle.legistar_file),
        jurisdiction=INTAKE_JURISDICTION,
        case_id=intake_case_id(bundle.legistar_file),
        case_topic=selection.case_topic,
        fixture_dir="",
        artifacts=artifacts,
        duplicate_event_fixture=None,
    )


def _manifest_artifact(
    bundle: CandidateBundle,
    attachment: CandidateAttachment,
    role: str,
    locked: FetchedAttachment,
    retrieved_at: datetime,
) -> ManifestArtifact:
    artifact_id = f"{intake_corpus_id(bundle.legistar_file)}-att{attachment.attachment_id}"
    return ManifestArtifact(
        artifact_id=artifact_id,
        role=role,
        source_id=INTAKE_SOURCE_ID,
        external_id=f"{bundle.legistar_file}/attachment/{attachment.attachment_id}",
        canonical_url=attachment.url,
        title=attachment.name,
        retrieved_at=retrieved_at,
        content_hash=locked.content_hash,
        media_type="application/pdf",
        local_path=f"records/{artifact_id}.pdf",
        availability=ArtifactAvailability.AVAILABLE,
        legistar_file=bundle.legistar_file,
        legistar_matter_id=bundle.matter_id,
        legistar_attachment_id=attachment.attachment_id,
        matter_url=bundle.matter_url,
        byte_length=locked.byte_length,
        page_count=locked.page_count,
    )
