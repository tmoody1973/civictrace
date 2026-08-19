"""Human-approval contracts (PRD FR-23). Pure: pydantic + stdlib.

A token authorizes exactly one action on exactly one artifact-hash for one case,
issued to one named reviewer, for a limited time. Anything else is a refusal.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import ApprovalActionType


class ApprovalToken(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token_id: str
    case_id: str
    artifact_hash: str
    action_type: ApprovalActionType
    reviewer_name: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None


class ApprovalCheck(BaseModel):
    """validate() result: ok, or exactly one plain-English refusal reason."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    reason: str | None = None
