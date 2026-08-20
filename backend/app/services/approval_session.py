"""Live local approval session: replayed ledger + ApprovalService + packet renderer in one place.

The API's write endpoints exist only against this session. A server built on a static
ledger.json stays read-only and says so. # ponytail: in-process session; Firestore-backed
approvals are the Slice 5 deploy work.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.domain.enums import ApprovalActionType, LedgerEventType
from app.repositories.cases import LedgerRecorder
from app.schemas.case import LedgerEvent
from app.schemas.corpus import CorpusManifest
from app.schemas.inquiry import InquiryProposal
from app.schemas.source import Artifact
from app.services.approval import DEFAULT_TTL, ApprovalService
from app.services.packet import (
    find_staged_delta,
    inquiry_artifact_hash,
    render_inquiry_packet,
)
from app.services.packet_store import LocalPacketWriter, PacketWriter
from app.services.replay import ReplayOptions, ReplayReport, replay_corpus
from app.services.uri_bytes import LocalUriResolver

HASH_MISMATCH_MESSAGE = "you approved different bytes than are staged"

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent
DEFAULT_PACKET_DIR = _BACKEND_ROOT / ".local-artifacts" / "packets"


def default_replay_options() -> ReplayOptions:
    """The reviewed fixture corpus, same paths as scripts/replay_corpus.py."""
    return ReplayOptions(
        manifest_path=_REPO_ROOT / "docs" / "sources" / "corpus-manifest.yaml",
        allowlist_path=_REPO_ROOT / "docs" / "sources" / "source-allowlist.yaml",
        extraction_path=_BACKEND_ROOT
        / "tests"
        / "fixtures"
        / "milwaukee-city-promise-ledger-demo-v1"
        / "fixture_extraction.json",
        fixture_root=_REPO_ROOT,
        vault_dir=_BACKEND_ROOT / ".local-artifacts" / "vault",
    )


@dataclass(frozen=True)
class ApproveOutcome:
    """Exactly one of these fields is the story; the route maps kind → HTTP status."""

    kind: str  # "ok" | "not_found" | "hash_mismatch" | "refused"
    reason: str | None = None
    token_id: str | None = None
    reviewer_name: str | None = None
    expires_at: datetime | None = None
    packet_hash: str | None = None
    packet_path: str | None = None


class ApprovalSession:
    """Owns one replayed case. Implements the TraceReader protocol, so reads stay live."""

    def __init__(
        self,
        report: ReplayReport,
        *,
        packet_writer: PacketWriter,
        clock: Callable[[], datetime],
        uri_resolver: LocalUriResolver | None = None,
    ) -> None:
        self._report = report
        self._ledger = report.ledger
        self._packet_writer = packet_writer
        self._uri_resolver = uri_resolver or LocalUriResolver()
        self._approval = ApprovalService(clock=clock, ledger=self._ledger)

    @classmethod
    def from_replay(
        cls,
        options: ReplayOptions,
        *,
        packet_dir: Path,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> ApprovalSession:
        return cls(
            replay_corpus(options, clock=clock),
            packet_writer=LocalPacketWriter(packet_dir),
            clock=clock,
        )

    @classmethod
    def from_cloud(
        cls,
        *,
        manifest: CorpusManifest,
        ledger: LedgerRecorder,
        packet_writer: PacketWriter,
        uri_resolver: LocalUriResolver,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> ApprovalSession:
        """Cloud API session (MOO-709): reads what the worker wrote; renders to the bucket."""
        report = ReplayReport(manifest=manifest, ledger=ledger)
        return cls(report, packet_writer=packet_writer, clock=clock, uri_resolver=uri_resolver)

    # --- TraceReader protocol --------------------------------------------------

    def case_ids(self) -> list[str]:
        return [self._report.manifest.case_id]

    def events_for_case(self, case_id: str) -> list[LedgerEvent] | None:
        if case_id != self._report.manifest.case_id:
            return None
        return self._ledger.events()

    def case_topic(self, case_id: str) -> str:
        return self._report.manifest.case_topic

    def artifact(self, artifact_id: str) -> Artifact | None:
        recorded = (
            event.artifact
            for event in self._ledger.events()
            if event.artifact is not None and event.artifact.artifact_id == artifact_id
        )
        return next(recorded, None)

    # --- Approval gateway ------------------------------------------------------

    @property
    def ttl_minutes(self) -> int:
        return int(DEFAULT_TTL.total_seconds() // 60)

    def staged_inquiry(self, case_id: str) -> tuple[InquiryProposal, str] | None:
        events = self.events_for_case(case_id)
        if events is None:
            return None
        staged = [
            e for e in events if e.event_type is LedgerEventType.INQUIRY_STAGED and e.inquiry
        ]
        if not staged:
            return None
        inquiry = staged[-1].inquiry
        assert inquiry is not None
        return inquiry, inquiry_artifact_hash(inquiry)

    def approve(self, case_id: str, *, reviewer_name: str, artifact_hash: str) -> ApproveOutcome:
        staged = self.staged_inquiry(case_id)
        if staged is None:
            return ApproveOutcome(kind="not_found", reason=f"case {case_id!r} not found")
        inquiry, staged_hash = staged
        if artifact_hash != staged_hash:
            self._ledger.record_approval_event(
                "APPROVAL_REFUSED",
                case_id=case_id,
                actor=reviewer_name,
                reason=HASH_MISMATCH_MESSAGE,
            )
            return ApproveOutcome(kind="hash_mismatch", reason=HASH_MISMATCH_MESSAGE)

        token = self._approval.issue(
            case_id=case_id,
            artifact_hash=staged_hash,
            action_type=ApprovalActionType.RENDER_INQUIRY_PACKET,
            reviewer_name=reviewer_name,
        )
        events = self._ledger.events()
        result = render_inquiry_packet(
            bundle=self._ledger.build_case_bundle(trigger_artifact_id="", new_evidence_ids=[]),
            delta=find_staged_delta(events),
            inquiry=inquiry,
            events=events,
            token=token,
            approval=self._approval,
            ledger=self._ledger,
            writer=self._packet_writer,
        )
        if not result.ok:
            return ApproveOutcome(kind="refused", reason=result.reason)
        assert result.packet_hash is not None and result.packet_path is not None
        return ApproveOutcome(
            kind="ok",
            token_id=token.token_id,
            reviewer_name=token.reviewer_name,
            expires_at=token.expires_at,
            packet_hash=result.packet_hash,
            packet_path=result.packet_path,
        )

    def reject(self, case_id: str, *, reviewer_name: str, note: str) -> bool:
        if self.events_for_case(case_id) is None:
            return False
        self._approval.record_rejection(case_id=case_id, reviewer_name=reviewer_name, note=note)
        return True

    def packet(self, case_id: str) -> tuple[str, str, str] | None:
        """(markdown, packet_hash, packet_path) for the last rendered packet, or None."""
        events = self.events_for_case(case_id)
        if events is None:
            return None
        rendered = [
            e
            for e in events
            if e.event_type is LedgerEventType.PACKET_RENDERED and e.packet_path
        ]
        if not rendered:
            return None
        event = rendered[-1]
        assert event.packet_path is not None
        markdown = self._read_packet(event.packet_path)
        return markdown, event.payload_ref, event.packet_path

    def _read_packet(self, packet_path: str) -> str:
        if packet_path.startswith("gs://"):
            return self._uri_resolver.read_bytes(packet_path).decode("utf-8")
        return Path(packet_path).read_text()
