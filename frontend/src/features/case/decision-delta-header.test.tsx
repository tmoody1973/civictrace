import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DecisionDeltaHeader } from "@/features/case/decision-delta-header";
import { PromiseCard } from "@/features/case/promise-card";
import type { CaseSummaryView, LatestDeltaView } from "@/lib/api-types";

const delta: LatestDeltaView = {
  category: "REVISED",
  neutral_summary: "The 2024 Project Plan set costs at $700,000; Amendment No. 1 sets $2,345,000.",
  original_evidence_ids: ["ev-plan"],
  later_evidence_ids: ["ev-amend-1", "ev-amend-2"],
  what_is_established: ["Plan p.5: $700,000."],
  what_is_not_established: ["Why the amendment was needed."],
  next_evidence_needed: "2025 Annual TID Report",
  limitations: ["Both figures are up-to ceilings."],
  requires_human_review: true,
  review_outcome: "APPROVE",
  blocking_issues: [],
};

const summary = (state: CaseSummaryView["state"]): CaseSummaryView => ({
  case_id: "case-x",
  case_topic: "TID 121",
  state,
  counts: {
    artifacts_stored: 3,
    evidence_accepted: 8,
    not_published: 1,
    extractions_rejected: 0,
    deltas_proposed: 1,
    deltas_rejected: 0,
  },
  latest_delta: state === "NO_DELTA" ? null : delta,
  next_evidence_needed: null,
});

describe("DecisionDeltaHeader", () => {
  it("renders every validated field and the evidence chips", () => {
    render(<DecisionDeltaHeader delta={delta} />);
    expect(screen.getByTestId("delta-category")).toHaveTextContent("The later document revises the commitment");
    expect(screen.getByTestId("delta-summary")).toHaveTextContent("$2,345,000");
    expect(screen.getByTestId("delta-established")).toHaveTextContent("Plan p.5");
    expect(screen.getByTestId("delta-not-established")).toHaveTextContent("Why the amendment was needed.");
    expect(screen.getByTestId("delta-next-evidence")).toHaveTextContent("2025 Annual TID Report");
    expect(screen.getByTestId("delta-blocking")).toHaveTextContent("None recorded");
    expect(screen.getByTestId("delta-review-outcome")).toHaveTextContent("Reviewer: approved");
    expect(screen.getAllByRole("button", { name: /Show evidence ev-amend/ })).toHaveLength(2);
  });

  it("says 'Not available' for every section when there is no delta — never hides a row", () => {
    render(<DecisionDeltaHeader delta={null} />);
    expect(screen.getByTestId("delta-empty")).toHaveTextContent("No Decision Delta has been staged");
    for (const id of [
      "delta-summary",
      "delta-established",
      "delta-not-established",
      "delta-next-evidence",
      "delta-limitations",
      "delta-blocking",
      "delta-original-ids",
      "delta-later-ids",
    ]) {
      expect(screen.getByTestId(id)).toHaveTextContent("Not available");
    }
  });
});

describe("PromiseCard", () => {
  it.each([
    ["NO_DELTA", "No material change found"],
    ["DELTA_STAGED", "Change staged — awaiting human review"],
    ["HUMAN_REVIEW", "Reviewer flagged — needs a human"],
  ] as const)("labels %s in words", (state, label) => {
    render(<PromiseCard summary={summary(state)} />);
    expect(screen.getByTestId("state-badge")).toHaveTextContent(label);
    expect(screen.getByTestId("count-evidence_accepted")).toHaveTextContent("8");
  });
});
