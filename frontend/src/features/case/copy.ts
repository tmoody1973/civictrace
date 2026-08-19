// Every user-facing sentence for the case card lives here, so one test can check the whole
// vocabulary against the backend allegation-word policy. Wording follows
// .claude/rules/privacy-and-evidence.md "Product Language": say what the record states,
// what it does not establish, what the later document revises. Never why, never who is at fault.

import type { CaseState, DeltaCategory, ReviewOutcome } from "@/lib/api-types";

export const NOT_AVAILABLE = "Not available";

export const STATE_COPY: Record<CaseState, { label: string; detail: string }> = {
  NO_DELTA: { label: "No material change found", detail: "The later records supplied do not revise the commitment." },
  DELTA_STAGED: {
    label: "Change staged — awaiting human review",
    detail: "A later public record revises the commitment. The reviewer approved; a human decides next.",
  },
  HUMAN_REVIEW: {
    label: "Reviewer flagged — needs a human",
    detail: "The second-look reviewer found an issue. Nothing is staged until a human looks.",
  },
};

export const CATEGORY_COPY: Record<DeltaCategory, string> = {
  ADVANCED: "The later document advances the commitment",
  REVISED: "The later document revises the commitment",
  DEFERRED: "The later document defers the commitment",
  CONFLICTING: "The later document conflicts with the original record",
  EXPECTED_EVIDENCE_ARRIVED: "An expected later record has arrived",
  RECORD_GAP: "The public record has a gap",
};

export const REVIEW_OUTCOME_COPY: Record<ReviewOutcome, string> = {
  APPROVE: "Reviewer: approved",
  REVISE: "Reviewer: asked for revision",
  REJECT: "Reviewer: rejected",
  HUMAN_REVIEW: "Reviewer: sent to a human",
};

export const SECTION_COPY = {
  promiseCard: "Promise Card",
  decisionDelta: "Decision Delta",
  summary: "What changed, in the record's own terms",
  established: "What the public record establishes",
  notEstablished: "What the record does not establish",
  nextEvidence: "Next expected record",
  limitations: "Limitations of this comparison",
  blockingIssues: "Blocking issues",
  originalEvidence: "Original commitment evidence",
  laterEvidence: "Later record evidence",
  noDelta: "No Decision Delta has been staged for this case.",
  humanReviewRequired: "A human must review before anything leaves this system.",
} as const;

export const COUNT_COPY = {
  artifacts_stored: "Source documents preserved",
  evidence_accepted: "Evidence excerpts accepted",
  not_published: "Expected records not yet published",
  extractions_rejected: "Extractions refused by checks",
  deltas_proposed: "Decision Deltas proposed",
  deltas_rejected: "Decision Deltas refused by checks",
} as const;

/** Every string above, flattened, for the vocabulary test. */
export function allCaseCopy(): string[] {
  const texts: string[] = [NOT_AVAILABLE];
  for (const value of Object.values(STATE_COPY)) texts.push(value.label, value.detail);
  texts.push(...Object.values(CATEGORY_COPY), ...Object.values(REVIEW_OUTCOME_COPY));
  texts.push(...Object.values(SECTION_COPY), ...Object.values(COUNT_COPY));
  return texts;
}
