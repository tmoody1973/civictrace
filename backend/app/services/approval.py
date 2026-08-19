"""Deterministic approval service (PRD FR-23): issue, validate, revoke. Fails closed.

No model, no network. The optional ledger receives one event per human decision and
per refusal, so the audit trail shows every "no" with its reason.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable
from datetime import datetime, timedelta

from app.domain.enums import ApprovalActionType
from app.schemas.approval import ApprovalCheck, ApprovalToken

DEFAULT_TTL = timedelta(minutes=30)  # long enough to review a packet, short enough to go stale


class _NullLedger:
    def record_approval_event(self, *args: object, **kwargs: object) -> None:  # pragma: no cover
        return None


class ApprovalService:
    def __init__(
        self,
        *,
        clock: Callable[[], datetime],
        ledger: object | None = None,
        ttl: timedelta = DEFAULT_TTL,
    ) -> None:
        self._clock = clock
        self._ledger = ledger if ledger is not None else _NullLedger()
        self._ttl = ttl
        self._revoked: set[str] = set()
        self._issued: set[str] = set()

    def issue(
        self,
        *,
        case_id: str,
        artifact_hash: str,
        action_type: ApprovalActionType,
        reviewer_name: str,
    ) -> ApprovalToken:
        now = self._clock()
        token = ApprovalToken(
            token_id="tok_" + secrets.token_hex(16),
            case_id=case_id,
            artifact_hash=artifact_hash,
            action_type=action_type,
            reviewer_name=reviewer_name,
            issued_at=now,
            expires_at=now + self._ttl,
        )
        self._issued.add(token.token_id)
        self._record("INQUIRY_APPROVAL_ISSUED", case_id=case_id, actor=reviewer_name, token=token)
        return token

    def record_rejection(self, *, case_id: str, reviewer_name: str, note: str) -> None:
        """The human said no. That is a decision, and it goes in the ledger."""
        self._record(
            "INQUIRY_APPROVAL_REJECTED",
            case_id=case_id,
            actor=reviewer_name,
            reason=f"rejected by {reviewer_name}: {note}",
        )

    def validate(
        self,
        token: ApprovalToken | None,
        *,
        case_id: str,
        artifact_hash: str,
        action_type: ApprovalActionType,
    ) -> ApprovalCheck:
        reason = self._refusal_reason(
            token, case_id=case_id, artifact_hash=artifact_hash, action_type=action_type
        )
        if reason is None:
            return ApprovalCheck(ok=True)
        self._record("APPROVAL_REFUSED", case_id=case_id, actor="system", reason=reason)
        return ApprovalCheck(ok=False, reason=reason)

    def revoke(self, token_id: str) -> bool:
        if token_id not in self._issued:
            return False
        self._revoked.add(token_id)
        return True

    def _refusal_reason(
        self,
        token: ApprovalToken | None,
        *,
        case_id: str,
        artifact_hash: str,
        action_type: ApprovalActionType,
    ) -> str | None:
        if token is None:
            return "approval token missing"
        if token.token_id in self._revoked or token.revoked_at is not None:
            return f"approval token {token.token_id} was revoked"
        if token.case_id != case_id:
            return f"case mismatch: token is for {token.case_id!r}, request is for {case_id!r}"
        if token.artifact_hash != artifact_hash:
            return "artifact hash mismatch: the approved bytes are not the bytes requested"
        if token.action_type is not action_type:
            return f"action mismatch: token allows {token.action_type}, not {action_type}"
        now = self._clock()
        if now >= token.expires_at:
            return f"approval token expired at {token.expires_at.isoformat()}"
        return None

    def _record(
        self,
        kind: str,
        *,
        case_id: str,
        actor: str,
        token: ApprovalToken | None = None,
        reason: str | None = None,
    ) -> None:
        recorder = getattr(self._ledger, "record_approval_event", None)
        if recorder is not None:
            recorder(kind, case_id=case_id, actor=actor, token=token, reason=reason)
