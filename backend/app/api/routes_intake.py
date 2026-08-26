"""Case-intake endpoints (MOO-719): official lookup → human review → gated creation.

The API never creates a case in the request: approval marks durable state and hands the
work to the creation runner (a Cloud Task in the cloud, an injected inline runner in
tests). A server wired without intake says so instead of failing silently.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.repositories.intake import IntakeStore
from app.schemas.api import ApiEnvelope
from app.schemas.intake import (
    BundleStatus,
    CandidateBundle,
    IntakeSelection,
    MatterSearchResult,
)

router = APIRouter()


class BundleLookup(Protocol):
    def candidate_bundle(self, file_number: str) -> CandidateBundle: ...
    def search_matters(self, query: str) -> list[MatterSearchResult]: ...


class IntakeGateway:
    """Everything the intake routes may touch, wired once at app assembly."""

    def __init__(
        self,
        *,
        lookup: BundleLookup,
        store: IntakeStore,
        start_creation: Callable[[str], None],
    ) -> None:
        self.lookup = lookup
        self.store = store
        self.start_creation = start_creation


class IntakeLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_number: str = Field(min_length=1, max_length=16)


class IntakeSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=200)


@router.post("/intake/search", response_model=ApiEnvelope[list[MatterSearchResult]])
def intake_search(
    payload: IntakeSearchRequest, request: Request
) -> ApiEnvelope[list[MatterSearchResult]] | JSONResponse:
    """Plain words in, official matters out (MOO-749). An empty list is an honest answer."""
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, "case intake is not enabled on this server")
    from app.services.legistar_intake import IntakeLookupError

    try:
        results = gateway.lookup.search_matters(payload.query)
    except IntakeLookupError as exc:
        return _error(422, str(exc))
    except OSError:
        return _error(502, "the official Legistar API could not be reached; try again")
    return ApiEnvelope(ok=True, data=results, error=None)


@router.post("/intake/lookup", response_model=ApiEnvelope[CandidateBundle])
def intake_lookup(
    payload: IntakeLookupRequest, request: Request
) -> ApiEnvelope[CandidateBundle] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, "case intake is not enabled on this server")
    from app.services.legistar_intake import IntakeLookupError

    try:
        bundle = gateway.lookup.candidate_bundle(payload.file_number)
    except IntakeLookupError as exc:
        return _error(422, str(exc))
    except OSError:
        return _error(502, "the official Legistar API could not be reached; try again")
    gateway.store.save_bundle(bundle)
    return ApiEnvelope(ok=True, data=bundle, error=None)


@router.get("/intake/bundles/{bundle_id}", response_model=ApiEnvelope[CandidateBundle])
def intake_bundle(bundle_id: str, request: Request) -> ApiEnvelope[CandidateBundle] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, "case intake is not enabled on this server")
    bundle = gateway.store.get_bundle(bundle_id)
    if bundle is None:
        return _error(404, f"bundle {bundle_id!r} not found")
    return ApiEnvelope(ok=True, data=bundle, error=None)


@router.post("/intake/bundles/{bundle_id}/approve", response_model=ApiEnvelope[CandidateBundle])
def intake_approve(
    bundle_id: str, selection: IntakeSelection, request: Request
) -> ApiEnvelope[CandidateBundle] | JSONResponse:
    gateway = _gateway(request)
    if gateway is None:
        return _error(503, "case intake is not enabled on this server")
    bundle = gateway.store.get_bundle(bundle_id)
    if bundle is None:
        return _error(404, f"bundle {bundle_id!r} not found")
    if bundle.status is not BundleStatus.DRAFT:
        return _error(409, f"bundle {bundle_id!r} is {bundle.status}; only a DRAFT can be approved")
    listed = {attachment.attachment_id for attachment in bundle.attachments}
    named = set(selection.promise_attachment_ids) | set(selection.later_attachment_ids)
    if not named <= listed:
        return _error(
            422, f"selection names attachments the record never listed: {sorted(named - listed)}"
        )
    gateway.store.save_selection(bundle_id, selection)
    gateway.store.set_status(bundle_id, BundleStatus.APPROVED)
    gateway.start_creation(bundle_id)
    approved = gateway.store.get_bundle(bundle_id)
    assert approved is not None
    return ApiEnvelope(ok=True, data=approved, error=None)


def _gateway(request: Request) -> IntakeGateway | None:
    return getattr(request.app.state, "intake", None)


def _error(status_code: int, message: str) -> JSONResponse:
    envelope: ApiEnvelope[None] = ApiEnvelope(ok=False, data=None, error=message)
    return JSONResponse(status_code=status_code, content=envelope.model_dump(mode="json"))
