"""Source watcher records (Slice 8.1, MOO-721). Pure: pydantic + stdlib.

A WatchHit is an OBSERVATION, never a conclusion: the official record lists something
this case has not reviewed yet. Every field is verbatim Legistar data plus provenance
(which API URL, when). A hit becomes case evidence only through the human intake gate.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class WatchHitKind(StrEnum):
    NEW_ACTION = "NEW_ACTION"
    NEW_ATTACHMENT = "NEW_ATTACHMENT"
    STATUS_CHANGE = "STATUS_CHANGE"
    EXPECTED_RECORD_CANDIDATE = "EXPECTED_RECORD_CANDIDATE"


class WatchHit(BaseModel):
    """One observed official-record item this case has not reviewed. Verbatim + provenance."""

    model_config = ConfigDict(extra="forbid")

    kind: WatchHitKind
    case_id: str
    matter_id: int | None = None
    legistar_file: str | None = None
    observed_at: datetime
    source_url: str
    # NEW_ACTION (verbatim history row)
    history_id: int | None = None
    action_name: str | None = None
    action_date: str | None = None
    passed_flag: str | None = None
    # NEW_ATTACHMENT (verbatim attachment row)
    attachment_id: int | None = None
    attachment_name: str | None = None
    attachment_url: str | None = None
    # STATUS_CHANGE (verbatim before/after)
    status_before: str | None = None
    status_after: str | None = None
    # EXPECTED_RECORD_CANDIDATE (a search match, never a confirmed link)
    expected_artifact_id: str | None = None
    candidate_title: str | None = None

    def payload_ref(self) -> str:
        parts = {
            WatchHitKind.NEW_ACTION: f"history/{self.history_id}",
            WatchHitKind.NEW_ATTACHMENT: f"attachment/{self.attachment_id}",
            WatchHitKind.STATUS_CHANGE: f"status/{self.status_after}",
            WatchHitKind.EXPECTED_RECORD_CANDIDATE: (
                f"expected/{self.expected_artifact_id}/matter/{self.matter_id}"
            ),
        }
        return f"watch/{self.case_id}/matter/{self.matter_id}/{parts[self.kind]}"


class WatchState(BaseModel):
    """Watermark per (case, matter): what the watcher has already reported. A no-hit run
    still updates checked_at — absence of news is recorded, never concluded from."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    matter_id: int | None = None
    legistar_file: str | None = None
    seen_history_ids: list[int] = Field(default_factory=list)
    seen_attachment_ids: list[int] = Field(default_factory=list)
    seen_candidate_matter_ids: list[int] = Field(default_factory=list)
    matter_status: str | None = None
    checked_at: datetime | None = None


def watch_state_key(case_id: str, matter_id: int | None, suffix: str = "") -> str:
    return f"{case_id}--{matter_id if matter_id is not None else suffix or 'expected'}"
