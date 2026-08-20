"""Deterministic inquiry-packet renderer (PRD FR-24). Draft-only, token-gated, fails closed.

Every line of the packet comes from a validated ledger/schema field. There is no free-text
generation here, no model, and no send path. The token's artifact_hash binds to the sha256
of the staged inquiry JSON — the exact bytes the human approved — so any later edit to the
inquiry invalidates the approval.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import ApprovalActionType, LedgerEventType
from app.schemas.approval import ApprovalToken
from app.schemas.case import BundleEvidence, CaseBundle, DecisionDeltaProposal, LedgerEvent
from app.schemas.inquiry import InquiryProposal
from app.services.approval import ApprovalService
from app.services.artifact_vault import HASH_PREFIX
from app.services.packet_store import PacketWriter

MILESTONE_EVENTS = (
    LedgerEventType.ARTIFACT_STORED,
    LedgerEventType.ARTIFACT_NOT_PUBLISHED,
    LedgerEventType.DELTA_STAGED,
    LedgerEventType.INQUIRY_STAGED,
)
DRAFT_NOTICE = "**DRAFT ONLY — not sent; no external action taken.**"


class PacketLedger(Protocol):
    def record_packet_rendered(
        self, *, case_id: str, actor: str, packet_hash: str, packet_path: str, token: ApprovalToken
    ) -> None: ...


@dataclass(frozen=True)
class PacketResult:
    ok: bool
    reason: str | None = None
    packet_path: str | None = None  # local filesystem path, or gs:// URI in the cloud
    packet_hash: str | None = None


def inquiry_artifact_hash(inquiry: InquiryProposal) -> str:
    """sha256 of the canonical inquiry JSON — the bytes the reviewer approves."""
    canonical = json.dumps(inquiry.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return HASH_PREFIX + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def find_staged_delta(events: list[LedgerEvent]) -> DecisionDeltaProposal:
    staged = [e for e in events if e.event_type is LedgerEventType.DELTA_STAGED and e.delta]
    if not staged:
        raise ValueError("no DELTA_STAGED event in the ledger")
    delta = staged[-1].delta
    assert delta is not None
    return delta


def find_staged_inquiry(events: list[LedgerEvent]) -> InquiryProposal:
    staged = [e for e in events if e.event_type is LedgerEventType.INQUIRY_STAGED and e.inquiry]
    if not staged:
        raise ValueError("no INQUIRY_STAGED event in the ledger")
    inquiry = staged[-1].inquiry
    assert inquiry is not None
    return inquiry


def render_inquiry_packet(
    *,
    bundle: CaseBundle,
    delta: DecisionDeltaProposal,
    inquiry: InquiryProposal,
    events: list[LedgerEvent],
    token: ApprovalToken | None,
    approval: ApprovalService,
    ledger: PacketLedger,
    writer: PacketWriter,
) -> PacketResult:
    """Validate the token against the staged inquiry's hash; refuse closed or write one file."""
    check = approval.validate(
        token,
        case_id=bundle.case_id,
        artifact_hash=inquiry_artifact_hash(inquiry),
        action_type=ApprovalActionType.RENDER_INQUIRY_PACKET,
    )
    if not check.ok or token is None:
        return PacketResult(ok=False, reason=check.reason)

    markdown = _build_markdown(
        bundle=bundle, delta=delta, inquiry=inquiry, events=events, token=token
    )
    packet_hash = HASH_PREFIX + hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    short_hash = packet_hash.removeprefix(HASH_PREFIX)[:12]
    packet_address = writer.write(
        f"inquiry-packet-{bundle.case_id}-{short_hash}.md", markdown
    )
    ledger.record_packet_rendered(
        case_id=bundle.case_id,
        actor=token.reviewer_name,
        packet_hash=packet_hash,
        packet_path=packet_address,
        token=token,
    )
    return PacketResult(ok=True, packet_path=packet_address, packet_hash=packet_hash)


def _build_markdown(
    *,
    bundle: CaseBundle,
    delta: DecisionDeltaProposal,
    inquiry: InquiryProposal,
    events: list[LedgerEvent],
    token: ApprovalToken,
) -> str:
    sections = [
        f"# DRAFT — Inquiry Packet — {bundle.case_id}",
        DRAFT_NOTICE,
        f"## Case\n{bundle.case_topic}",
        _chronology(events),
        _delta_section(delta),
        _excerpts("Original commitment (anchored excerpts)", bundle.original_evidence),
        _excerpts("Later evidence (anchored excerpts)", bundle.later_evidence),
        _sources(events),
        _inquiry_section(inquiry),
        _approval_section(token),
    ]
    return "\n\n".join(sections) + "\n"


def _chronology(events: list[LedgerEvent]) -> str:
    lines = ["## Case chronology (ledger milestones)"]
    for event in events:
        if event.event_type not in MILESTONE_EVENTS:
            continue
        day = event.occurred_at.date().isoformat()
        lines.append(f"- {day} — {event.event_type} — {event.payload_ref}")
    return "\n".join(lines)


def _delta_section(delta: DecisionDeltaProposal) -> str:
    lines = [
        f"## Decision Delta ({delta.category})",
        delta.neutral_summary,
        "",
        "### What the record establishes",
        *[f"- {line}" for line in delta.what_is_established],
        "",
        "### What the record does not establish",
        *[f"- {line}" for line in delta.what_is_not_established],
    ]
    if delta.limitations:
        lines += ["", "### Limitations", *[f"- {line}" for line in delta.limitations]]
    return "\n".join(lines)


def _excerpts(title: str, items: list[BundleEvidence]) -> str:
    lines = [f"## {title}"]
    for item in items:
        evidence = item.evidence
        anchors = ", ".join(f"{a.anchor_type} {a.anchor_value}" for a in evidence.anchors)
        lines.append(
            f'- **{evidence.evidence_id}** — "{evidence.verbatim_excerpt}"'
            f" ({anchors}; {evidence.artifact_id})"
        )
    return "\n".join(lines)


def _sources(events: list[LedgerEvent]) -> str:
    lines = [
        "## Sources (preserved public artifacts)",
        "| Artifact | Canonical URL | Retrieved | sha256 |",
        "|---|---|---|---|",
    ]
    seen: set[str] = set()
    for event in events:
        artifact = event.artifact
        if artifact is None or artifact.artifact_id in seen:
            continue
        if event.event_type not in (
            LedgerEventType.ARTIFACT_STORED,
            LedgerEventType.ARTIFACT_NOT_PUBLISHED,
        ):
            continue
        seen.add(artifact.artifact_id)
        retrieved = artifact.retrieved_at.isoformat()
        content_hash = artifact.content_hash or "NOT_PUBLISHED"
        lines.append(
            f"| {artifact.artifact_id} | {artifact.canonical_url or '—'}"
            f" | {retrieved} | {content_hash} |"
        )
    return "\n".join(lines)


def _inquiry_section(inquiry: InquiryProposal) -> str:
    lines = [
        f"## Proposed next question ({inquiry.inquiry_type})",
        f"**Question.** {inquiry.proposed_question}",
        "",
        f"**Why this scope.** {inquiry.scope_rationale}",
        "",
        f"**Target record or source.** {inquiry.target_record_or_source}",
        "",
        "**Cited evidence.** " + ", ".join(inquiry.supporting_evidence_ids),
        "",
        "### Expressly excluded",
        *[f"- {line}" for line in inquiry.excluded_requests],
    ]
    if inquiry.limitations:
        lines += ["", "### Limitations", *[f"- {line}" for line in inquiry.limitations]]
    return "\n".join(lines)


def _approval_section(token: ApprovalToken) -> str:
    return "\n".join(
        [
            "## Approval",
            f"- Reviewer: {token.reviewer_name}",
            f"- Token: {token.token_id}",
            f"- Action: {token.action_type}",
            f"- Approved inquiry hash: {token.artifact_hash}",
            f"- Issued: {token.issued_at.isoformat()}  ·  Expires: {token.expires_at.isoformat()}",
        ]
    )
