// Hand-written mirror of backend/app/schemas/api.py (MOO-695). Keep the two in step by hand;
// ponytail: generate from OpenAPI once the contract stops moving (Slice 5).

export type ApiEnvelope<T> = { ok: true; data: T; error: null } | { ok: false; data: null; error: string };

export type CaseState = "NO_DELTA" | "DELTA_STAGED" | "HUMAN_REVIEW";

export type LedgerEventType =
  | "ARTIFACT_STORED"
  | "ARTIFACT_NOT_PUBLISHED"
  | "EVIDENCE_ACCEPTED"
  | "ENTITY_LINKED"
  | "EXTRACTION_REJECTED"
  | "NO_MATERIAL_DELTA"
  | "DELTA_PROPOSED"
  | "DELTA_REJECTED"
  | "DELTA_STAGED"
  | "CASE_HUMAN_REVIEW"
  | "INQUIRY_STAGED"
  | "INQUIRY_REJECTED"
  | "INQUIRY_APPROVAL_ISSUED"
  | "INQUIRY_APPROVAL_REJECTED"
  | "APPROVAL_REFUSED"
  | "PACKET_RENDERED";

export type InquiryType = "SOURCE_QUESTION" | "RECORDS_REQUEST_OUTLINE" | "WATCH_REMINDER" | "HUMAN_RESEARCH_TASK";

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
  media_type: string | null;
  evidence_id: string | null;
  entity_id: string | null;
  link_status: string | null;
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
  inquiry_type: InquiryType | null;
  proposed_question: string | null;
  scope_rationale: string | null;
  target_record_or_source: string | null;
  supporting_evidence_ids: string[];
  excluded_requests: string[];
  approval_token_id: string | null;
  approval_reviewer: string | null;
  approval_expires_at: string | null;
  review_outcome: ReviewOutcome | null;
  blocking_issues: string[];
  review_notes: string[];
}

export interface InquiryProposalView {
  inquiry_type: InquiryType;
  proposed_question: string;
  scope_rationale: string;
  target_record_or_source: string;
  supporting_evidence_ids: string[];
  excluded_requests: string[];
  approval_required: boolean;
  limitations: string[];
}

export interface InquiryStagedView {
  case_id: string;
  proposal: InquiryProposalView;
  artifact_hash: string;
  ttl_minutes: number;
}

export interface ApprovalResultView {
  token_id: string;
  reviewer_name: string;
  expires_at: string;
  packet_hash: string;
  packet_path: string;
}

export interface PacketView {
  case_id: string;
  markdown: string;
  packet_hash: string;
  packet_path: string;
}

export interface TraceResponse {
  case_id: string;
  events: TraceEventView[];
}

export type BundleStatus = "DRAFT" | "APPROVED" | "CREATING" | "CASE_CREATED" | "FAILED";

export interface MatterSearchResultView {
  legistar_file: string;
  matter_id: number;
  title: string;
  matter_type: string | null;
  matter_status: string | null;
  intro_date: string | null;
}

export interface CandidateAttachmentView {
  attachment_id: number;
  name: string;
  url: string;
}

export interface CandidateBundleView {
  bundle_id: string;
  legistar_file: string;
  matter_id: number;
  title: string;
  matter_type: string | null;
  matter_status: string | null;
  intro_date: string | null;
  matter_url: string;
  attachments: CandidateAttachmentView[];
  retrieved_at: string;
  status: BundleStatus;
  failure_reason: string | null;
  case_id: string | null;
}

export interface IntakeSelectionPayload {
  reviewer_name: string;
  case_topic: string;
  promise_attachment_ids: number[];
  later_attachment_ids: number[];
}

export interface TranscriptSegmentView {
  start_ms: number;
  end_ms: number;
  speaker_label: string;
  text: string;
  confidence: number | null;
}

export interface TranscriptView {
  transcript_id: string;
  artifact_id: string;
  segment_start_seconds: number;
  segment_end_seconds: number;
  stt_provider: string;
  stt_model: string;
  diarization: boolean;
  confidence_note: string;
  segments: TranscriptSegmentView[];
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
  last_event_at: string | null;
}
