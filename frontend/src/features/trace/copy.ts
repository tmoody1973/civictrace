// All Evidence Trace wording. Checked by the same vocabulary test as the case copy.

import type { LedgerEventType } from "@/lib/api-types";

export const TRACE_COPY = {
  header: (rows: number, artifacts: number) => `Evidence Trace · ${rows} rows · ${artifacts} source artifacts`,
  quote: "Verbatim excerpt from the record",
  statement: "Neutral statement",
  anchors: "Where in the record",
  openSource: "Open official source",
  hash: "Fingerprint (SHA-256) of the saved copy",
  humanStep: "Human decision required",
  humanStepDetail: "A narrow next step is staged. No external action happens without a human approval.",
  notPublishedLabel: "NOT_PUBLISHED",
  limitations: "Limitations",
  reviewNotes: "Reviewer notes",
  blockingIssues: "Blocking issues",
  reason: "Reason",
  proposedQuestion: "Proposed next question",
  established: "What the public record establishes",
  notEstablished: "What the record does not establish",
  nextEvidence: "Next expected record",
  noRows: "The ledger has no rows for this case yet.",
} as const;

export const EVENT_LABEL: Record<LedgerEventType, string> = {
  ARTIFACT_STORED: "Source preserved",
  ARTIFACT_NOT_PUBLISHED: "Expected record not published",
  EVIDENCE_ACCEPTED: "Evidence extracted and checked",
  ENTITY_LINKED: "Matched to something the system knows",
  EXTRACTION_REJECTED: "Extraction refused by checks",
  NO_MATERIAL_DELTA: "No material change found",
  DELTA_PROPOSED: "Later evidence compared",
  DELTA_REJECTED: "Proposed change refused by checks",
  DELTA_STAGED: "Change staged for human review",
  CASE_HUMAN_REVIEW: "Sent to a human reviewer",
  INQUIRY_STAGED: "Next question staged for approval",
  INQUIRY_REJECTED: "Proposed question refused by checks",
  INQUIRY_APPROVAL_ISSUED: "Human approved — token issued",
  INQUIRY_APPROVAL_REJECTED: "Human rejected the proposed question",
  APPROVAL_REFUSED: "Approval refused — failed closed",
  PACKET_RENDERED: "DRAFT packet rendered",
};

export const EVIDENCE_STATUS_LABEL: Record<string, string> = {
  SUPPORTED: "Supported by the record",
  UNKNOWN: "Unknown — the record does not say",
  NOT_PUBLISHED: "Not published",
  CONFLICTING: "Conflicting records",
  CANDIDATE_LINK: "Candidate link, not confirmed",
  REQUEST_NEEDED: "Records request needed",
  HUMAN_REVIEW: "Needs a human",
};

export function allTraceCopy(): string[] {
  const texts: string[] = [TRACE_COPY.header(0, 0)];
  for (const value of Object.values(TRACE_COPY)) if (typeof value === "string") texts.push(value);
  texts.push(...Object.values(EVENT_LABEL), ...Object.values(EVIDENCE_STATUS_LABEL));
  return texts;
}
