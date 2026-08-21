// Pure mapping: one validated ledger row (TraceEventView) → what the UI shows. No fetch, no model text.
// The row reads contract fields only; row-model.test.ts proves it with a key-access proxy.

import { EVENT_LABEL } from "@/features/trace/copy";
import type { AnchorView, LedgerEventType, TraceEventView } from "@/lib/api-types";

export type StepStatus = "complete" | "active" | "pending";

export type TraceRow = {
  id: string;
  eventType: LedgerEventType;
  label: string;
  occurredAt: string;
  artifactId: string;
  canonicalUrl: string | null;
  status: string;
  stepStatus: StepStatus;
  isHuman: boolean;
  isGap: boolean;
  evidenceId: string | null;
  anchors: AnchorView[];
  event: TraceEventView;
};

const HUMAN_STEPS: ReadonlySet<LedgerEventType> = new Set([
  "DELTA_STAGED",
  "CASE_HUMAN_REVIEW",
  "INQUIRY_STAGED",
  "INQUIRY_APPROVAL_ISSUED",
  "INQUIRY_APPROVAL_REJECTED",
]);
const GAP_STEPS: ReadonlySet<LedgerEventType> = new Set([
  "ARTIFACT_NOT_PUBLISHED",
  "EXTRACTION_REJECTED",
  "DELTA_REJECTED",
  "INQUIRY_REJECTED",
  "APPROVAL_REFUSED",
]);

/** Gaps and human steps are never shown as "complete". */
export function stepStatusFor(eventType: LedgerEventType, status: string): StepStatus {
  if (HUMAN_STEPS.has(eventType)) return "active";
  if (GAP_STEPS.has(eventType)) return "pending";
  if (status === "UNKNOWN" || status === "CONFLICTING" || status === "HUMAN_REVIEW") return "pending";
  if (status === "CANDIDATE") return "pending"; // a possible entity match is never shown as settled
  return "complete";
}

export function toTraceRow(event: TraceEventView): TraceRow {
  return {
    id: event.event_id,
    eventType: event.event_type,
    label: EVENT_LABEL[event.event_type],
    occurredAt: event.occurred_at,
    artifactId: event.artifact_id,
    canonicalUrl: event.canonical_url,
    status: event.status,
    stepStatus: stepStatusFor(event.event_type, event.status),
    isHuman: HUMAN_STEPS.has(event.event_type),
    isGap: GAP_STEPS.has(event.event_type),
    evidenceId: event.evidence_id,
    anchors: event.anchors,
    event,
  };
}

export function pageOf(anchors: AnchorView[]): number | null {
  const page = anchors.find((anchor) => anchor.anchor_type === "page");
  const parsed = page ? Number.parseInt(page.anchor_value, 10) : Number.NaN;
  return Number.isFinite(parsed) ? parsed : null;
}

export function countArtifacts(events: TraceEventView[]): number {
  return new Set(events.filter((event) => event.event_type === "ARTIFACT_STORED").map((event) => event.artifact_id))
    .size;
}
