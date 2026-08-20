"""Approval + packet endpoints — the API's first writes, local only.

# ponytail: local write endpoints; auth is the Slice 5 deploy gate (reviewer is a typed name).
"""

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.schemas.api import (
    ApiEnvelope,
    ApprovalResultView,
    ApproveInquiryRequest,
    InquiryProposalView,
    InquiryStagedView,
    PacketView,
    RejectInquiryRequest,
)
from app.schemas.inquiry import InquiryProposal
from app.services.approval_session import ApproveOutcome

router = APIRouter()

NO_LIVE_SESSION = "approval needs the live server (started with CIVICTRACE_LIVE=1)"


class ApprovalGateway(Protocol):
    @property
    def ttl_minutes(self) -> int: ...
    def staged_inquiry(self, case_id: str) -> tuple[InquiryProposal, str] | None: ...
    def approve(
        self, case_id: str, *, reviewer_name: str, artifact_hash: str
    ) -> ApproveOutcome: ...
    def reject(self, case_id: str, *, reviewer_name: str, note: str) -> bool: ...
    def packet(self, case_id: str) -> tuple[str, str, str] | None: ...


def _error(status_code: int, message: str) -> JSONResponse:
    envelope: ApiEnvelope[None] = ApiEnvelope(ok=False, data=None, error=message)
    return JSONResponse(status_code=status_code, content=envelope.model_dump(mode="json"))


def _gateway(request: Request) -> ApprovalGateway | None:
    return getattr(request.app.state, "approval", None)


@router.get("/cases/{case_id}/inquiry", response_model=ApiEnvelope[InquiryStagedView])
def staged_inquiry(case_id: str, request: Request) -> ApiEnvelope[InquiryStagedView] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, NO_LIVE_SESSION)
    staged = gateway.staged_inquiry(case_id)
    if staged is None:
        return _error(404, f"case {case_id!r} not found or has no staged inquiry")
    inquiry, artifact_hash = staged
    view = InquiryStagedView(
        case_id=case_id,
        proposal=InquiryProposalView.model_validate(inquiry.model_dump()),
        artifact_hash=artifact_hash,
        ttl_minutes=gateway.ttl_minutes,
    )
    return ApiEnvelope(ok=True, data=view, error=None)


@router.post("/cases/{case_id}/inquiry/approve", response_model=ApiEnvelope[ApprovalResultView])
def approve_inquiry(
    case_id: str, body: ApproveInquiryRequest, request: Request
) -> ApiEnvelope[ApprovalResultView] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, NO_LIVE_SESSION)
    outcome = gateway.approve(
        case_id, reviewer_name=body.reviewer_name, artifact_hash=body.artifact_hash
    )
    if outcome.kind == "not_found":
        return _error(404, outcome.reason or "not found")
    if outcome.kind == "hash_mismatch":
        return _error(409, outcome.reason or "hash mismatch")
    if outcome.kind == "refused":
        return _error(409, outcome.reason or "approval refused")
    assert outcome.token_id and outcome.reviewer_name and outcome.expires_at
    assert outcome.packet_hash and outcome.packet_path
    view = ApprovalResultView(
        token_id=outcome.token_id,
        reviewer_name=outcome.reviewer_name,
        expires_at=outcome.expires_at,
        packet_hash=outcome.packet_hash,
        packet_path=outcome.packet_path,
    )
    return ApiEnvelope(ok=True, data=view, error=None)


@router.post("/cases/{case_id}/inquiry/reject", response_model=ApiEnvelope[None])
def reject_inquiry(
    case_id: str, body: RejectInquiryRequest, request: Request
) -> ApiEnvelope[None] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, NO_LIVE_SESSION)
    if not gateway.reject(case_id, reviewer_name=body.reviewer_name, note=body.note):
        return _error(404, f"case {case_id!r} not found")
    return ApiEnvelope(ok=True, data=None, error=None)


@router.get("/cases/{case_id}/packet", response_model=ApiEnvelope[PacketView])
def rendered_packet(case_id: str, request: Request) -> ApiEnvelope[PacketView] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, NO_LIVE_SESSION)
    packet = gateway.packet(case_id)
    if packet is None:
        return _error(404, "no packet has been rendered for this case")
    markdown, packet_hash, packet_path = packet
    view = PacketView(
        case_id=case_id, markdown=markdown, packet_hash=packet_hash, packet_path=packet_path
    )
    return ApiEnvelope(ok=True, data=view, error=None)
