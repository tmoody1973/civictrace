from __future__ import annotations

from fastapi import APIRouter

from app.schemas.api import ApiEnvelope, HealthResponse

router = APIRouter()


@router.get("/healthz", response_model=ApiEnvelope[HealthResponse])
def healthz() -> ApiEnvelope[HealthResponse]:
    return ApiEnvelope(ok=True, data=HealthResponse(status="ok"), error=None)
