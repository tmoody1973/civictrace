"""MOO-702: the approval token binds case + exact bytes + action + reviewer + expiry,
and the service refuses everything else with a plain reason. Fail closed, always."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.enums import ApprovalActionType, LedgerEventType
from app.repositories.cases import InMemoryLedger
from app.schemas.approval import ApprovalToken
from app.services.approval import DEFAULT_TTL, ApprovalService

NOW = datetime(2026, 8, 19, 18, 0, tzinfo=UTC)
CASE = "case-tid121-bronzeville-arts-tech-hub"
HASH = "sha256:aaaa"
ACTION = ApprovalActionType.RENDER_INQUIRY_PACKET


def _service(now: datetime = NOW) -> ApprovalService:
    return ApprovalService(clock=lambda: now)


def _issue(service: ApprovalService) -> ApprovalToken:
    return service.issue(
        case_id=CASE, artifact_hash=HASH, action_type=ACTION, reviewer_name="Tarik Moody"
    )


def test_issue_then_validate_passes_and_carries_the_bindings() -> None:
    service = _service()
    token = _issue(service)
    assert token.case_id == CASE
    assert token.artifact_hash == HASH
    assert token.reviewer_name == "Tarik Moody"
    assert token.expires_at == NOW + DEFAULT_TTL
    check = service.validate(token, case_id=CASE, artifact_hash=HASH, action_type=ACTION)
    assert check.ok and check.reason is None


def test_every_mismatch_refuses_with_a_plain_reason() -> None:
    service = _service()
    token = _issue(service)
    cases = {
        "case mismatch": dict(case_id="case-other", artifact_hash=HASH, action_type=ACTION),
        "artifact hash mismatch": dict(
            case_id=CASE, artifact_hash="sha256:bbbb", action_type=ACTION
        ),
    }
    for expected, kwargs in cases.items():
        check = service.validate(token, **kwargs)
        assert not check.ok and expected in (check.reason or ""), expected


def test_missing_token_refuses() -> None:
    check = _service().validate(None, case_id=CASE, artifact_hash=HASH, action_type=ACTION)
    assert not check.ok and "missing" in (check.reason or "")


def test_expiry_boundary_valid_just_before_refused_at_expiry() -> None:
    service = _service()
    token = _issue(service)
    just_before = ApprovalService(clock=lambda: token.expires_at - timedelta(seconds=1))
    at_expiry = ApprovalService(clock=lambda: token.expires_at)
    assert just_before.validate(token, case_id=CASE, artifact_hash=HASH, action_type=ACTION).ok
    check = at_expiry.validate(token, case_id=CASE, artifact_hash=HASH, action_type=ACTION)
    assert not check.ok and "expired" in (check.reason or "")


def test_revoke_wins_and_stays_revoked() -> None:
    service = _service()
    token = _issue(service)
    service.revoke(token.token_id)
    for _ in range(2):  # a second validate must not bypass via any cache
        check = service.validate(token, case_id=CASE, artifact_hash=HASH, action_type=ACTION)
        assert not check.ok and "revoked" in (check.reason or "")


def test_unknown_token_id_cannot_be_revoked_silently() -> None:
    assert _service().revoke("tok_nope") is False


def test_ledger_records_issue_reject_and_refusal_rows() -> None:
    ledger = InMemoryLedger(
        case_id=CASE, clock=lambda: NOW, original_artifact_ids=frozenset(), case_topic=""
    )
    service = ApprovalService(clock=lambda: NOW, ledger=ledger)
    token = _issue(service)
    service.record_rejection(
        case_id=CASE, reviewer_name="Tarik Moody", note="not yet — wait for the 2025 report"
    )
    service.validate(token, case_id=CASE, artifact_hash="sha256:tampered", action_type=ACTION)
    kinds = [event.event_type for event in ledger.events()]
    assert kinds == [
        LedgerEventType.INQUIRY_APPROVAL_ISSUED,
        LedgerEventType.INQUIRY_APPROVAL_REJECTED,
        LedgerEventType.APPROVAL_REFUSED,
    ]
    issued, rejected, refused = ledger.events()
    assert issued.approval is not None and issued.approval.token_id == token.token_id
    assert issued.actor == "Tarik Moody"
    assert rejected.reason and "wait for the 2025 report" in rejected.reason
    assert refused.reason and "artifact hash mismatch" in refused.reason


def test_valid_validate_does_not_write_a_refusal_row() -> None:
    ledger = InMemoryLedger(
        case_id=CASE, clock=lambda: NOW, original_artifact_ids=frozenset(), case_topic=""
    )
    service = ApprovalService(clock=lambda: NOW, ledger=ledger)
    token = _issue(service)
    assert service.validate(token, case_id=CASE, artifact_hash=HASH, action_type=ACTION).ok
    kinds = [event.event_type for event in ledger.events()]
    assert LedgerEventType.APPROVAL_REFUSED not in kinds
