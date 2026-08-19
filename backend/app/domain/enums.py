"""State machines and closed vocabularies. Pure: stdlib only.

User-facing uncertainty states are uppercase per CONTEXT.md.
"""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DUPLICATE_SUPPRESSED = "DUPLICATE_SUPPRESSED"
    NOT_PUBLISHED = "NOT_PUBLISHED"
    NO_ACTION = "NO_ACTION"


class ArtifactAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    NOT_PUBLISHED = "NOT_PUBLISHED"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"


class AnchorType(StrEnum):
    PAGE = "page"
    TABLE_CELL = "table_cell"
    DATASET_ROW = "dataset_row"
    TRANSCRIPT_TIME = "transcript_time"
    VIDEO_TIME = "video_time"
    MAP_FEATURE = "map_feature"


class EvidenceObjectType(StrEnum):
    COMMITMENT = "COMMITMENT"
    DECISION = "DECISION"
    ACTION_ITEM = "ACTION_ITEM"
    VOTE = "VOTE"
    CLAIM = "CLAIM"
    UNKNOWN = "UNKNOWN"


class EvidenceStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"
    NOT_PUBLISHED = "NOT_PUBLISHED"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class LinkStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    CANDIDATE = "CANDIDATE"
    REJECTED = "REJECTED"


class DeltaCategory(StrEnum):
    ADVANCED = "ADVANCED"
    REVISED = "REVISED"
    DEFERRED = "DEFERRED"
    CONFLICTING = "CONFLICTING"
    EXPECTED_EVIDENCE_ARRIVED = "EXPECTED_EVIDENCE_ARRIVED"
    RECORD_GAP = "RECORD_GAP"


class ReviewOutcome(StrEnum):
    APPROVE = "APPROVE"
    REVISE = "REVISE"
    BLOCK = "BLOCK"
