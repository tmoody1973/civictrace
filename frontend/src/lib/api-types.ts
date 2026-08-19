// Hand-written mirror of backend/app/schemas/api.py (MOO-695). Keep the two in step by hand;
// ponytail: generate from OpenAPI once the contract stops moving (Slice 5).

export type ApiEnvelope<T> = { ok: true; data: T; error: null } | { ok: false; data: null; error: string };

export type CaseState = "NO_DELTA" | "DELTA_STAGED" | "HUMAN_REVIEW";

export type LedgerEventType =
  | "ARTIFACT_STORED"
  | "ARTIFACT_NOT_PUBLISHED"
  | "EVIDENCE_ACCEPTED"
  | "EXTRACTION_REJECTED"
  | "NO_MATERIAL_DELTA"
  | "DELTA_PROPOSED"
  | "DELTA_REJECTED"
  | "DELTA_STAGED"
  | "CASE_HUMAN_REVIEW";

export type AnchorType = "page" | "table_cell" | "dataset_row" | "transcript_time" | "video_time" | "map_feature";
export type DeltaCategory = "ADVANCED" | "REVISED" | "DEFERRED" | "CONFLICTING" | "EXPECTED_EVIDENCE_ARRIVED" | "RECORD_GAP";
export type ReviewOutcome = "APPROVE" | "REVISE" | "REJECT" | "HUMAN_REVIEW";

export interface HealthResponse {
  status: string;
}

export interface AnchorView {
  anchor_type: AnchorType;
  anchor_value: string;
}

export interface TraceEventView {
  event_id: string;
  event_type: LedgerEventType;
  occurred_at: string;
  actor: string;
  artifact_id: string;
  canonical_url: string | null;
  status: string;
  content_hash: string | null;
  evidence_id: string | null;
  anchors: AnchorView[];
  verbatim_excerpt: string | null;
  neutral_statement: string | null;
  limitations: string[];
  reason: string | null;
  category: DeltaCategory | null;
  neutral_summary: string | null;
  original_evidence_ids: string[];
  later_evidence_ids: string[];
  what_is_established: string[];
  what_is_not_established: string[];
  next_evidence_needed: string | null;
  requires_human_review: boolean | null;
  review_outcome: ReviewOutcome | null;
  blocking_issues: string[];
  review_notes: string[];
}

export interface TraceResponse {
  case_id: string;
  events: TraceEventView[];
}

export interface CaseCounts {
  artifacts_stored: number;
  evidence_accepted: number;
  not_published: number;
  extractions_rejected: number;
  deltas_proposed: number;
  deltas_rejected: number;
}

export interface LatestDeltaView {
  category: DeltaCategory;
  neutral_summary: string;
  original_evidence_ids: string[];
  later_evidence_ids: string[];
  what_is_established: string[];
  what_is_not_established: string[];
  next_evidence_needed: string | null;
  limitations: string[];
  requires_human_review: boolean;
  review_outcome: ReviewOutcome | null;
  blocking_issues: string[];
}

export interface CaseSummaryView {
  case_id: string;
  case_topic: string;
  state: CaseState;
  counts: CaseCounts;
  latest_delta: LatestDeltaView | null;
  next_evidence_needed: string | null;
}
