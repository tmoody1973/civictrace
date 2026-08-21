import { describe, expect, it } from "vitest";

import fixture from "@/features/trace/__fixtures__/tid121-trace.json";
import { countArtifacts, pageOf, stepStatusFor, toTraceRow } from "@/features/trace/row-model";
import type { TraceEventView, TraceResponse } from "@/lib/api-types";

const trace = fixture as TraceResponse;

// Keys that exist on the API contract (backend/app/schemas/api.py TraceEventView).
const CONTRACT_KEYS = new Set<keyof TraceEventView>([
  "event_id", "event_type", "occurred_at", "actor", "artifact_id", "canonical_url", "status", "content_hash", "media_type", "entity_id", "link_status",
  "evidence_id", "anchors", "verbatim_excerpt", "neutral_statement", "limitations", "reason", "category",
  "neutral_summary", "original_evidence_ids", "later_evidence_ids", "what_is_established",
  "what_is_not_established", "next_evidence_needed", "requires_human_review", "review_outcome",
  "blocking_issues", "review_notes",
]);

describe("toTraceRow", () => {
  it("reads only contract fields — never a free-text model field", () => {
    const touched = new Set<string>();
    const spied = new Proxy(trace.events[0], {
      get(target, key) {
        if (typeof key === "string") touched.add(key);
        return Reflect.get(target, key);
      },
    });
    toTraceRow(spied);
    for (const key of touched) expect(CONTRACT_KEYS.has(key as keyof TraceEventView)).toBe(true);
  });

  it("maps the real TID 121 ledger: human step active, gaps pending, evidence complete", () => {
    const rows = trace.events.map(toTraceRow);
    const byType = (t: string) => rows.filter((row) => row.eventType === t);
    expect(byType("ARTIFACT_STORED")).toHaveLength(3);
    expect(byType("DELTA_STAGED")[0]).toMatchObject({ isHuman: true, stepStatus: "active" });
    expect(byType("ARTIFACT_NOT_PUBLISHED")[0]).toMatchObject({ isGap: true, stepStatus: "pending" });
    const unknown = byType("EVIDENCE_ACCEPTED").find((row) => row.status === "UNKNOWN");
    expect(unknown?.stepStatus).toBe("pending");
    expect(byType("EVIDENCE_ACCEPTED").find((row) => row.status === "SUPPORTED")?.stepStatus).toBe("complete");
    expect(countArtifacts(trace.events)).toBe(3);
  });

  it("never marks a gap or a human step complete", () => {
    expect(stepStatusFor("CASE_HUMAN_REVIEW", "x")).toBe("active");
    expect(stepStatusFor("EXTRACTION_REJECTED", "x")).toBe("pending");
    expect(stepStatusFor("DELTA_REJECTED", "x")).toBe("pending");
    expect(stepStatusFor("EVIDENCE_ACCEPTED", "CONFLICTING")).toBe("pending");
  });

  it("reads the page anchor", () => {
    expect(pageOf([{ anchor_type: "page", anchor_value: "5" }])).toBe(5);
    expect(pageOf([{ anchor_type: "table_cell", anchor_value: "A1" }])).toBeNull();
  });
});
