from __future__ import annotations

from fastapi import APIRouter

from app.schemas.api import ApiEnvelope, HealthResponse

router = APIRouter()


# /healthz is kept for local tooling; Google's front end intercepts the exact path
# "/healthz" on run.app domains, so the cloud uses the /health alias.
@router.get("/healthz", response_model=ApiEnvelope[HealthResponse])
@router.get("/health", response_model=ApiEnvelope[HealthResponse])
def healthz() -> ApiEnvelope[HealthResponse]:
    return ApiEnvelope(ok=True, data=HealthResponse(status="ok"), error=None)
