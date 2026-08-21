import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import fixture from "@/features/trace/__fixtures__/tid121-trace.json";
import { focusEvidence } from "@/features/case/evidence-focus";
import { ARTIFACT_JUMP_EVENT } from "@/features/trace/artifact-jump";
import { EvidenceTraceView } from "@/features/trace/evidence-trace";
import type { TraceResponse } from "@/lib/api-types";

const trace = fixture as TraceResponse;

describe("EvidenceTraceView (real TID 121 ledger rows)", () => {
  it("is collapsed by default and shows the counts in the header", () => {
    render(<EvidenceTraceView events={trace.events} />);
    expect(screen.getByRole("button", { name: /Toggle Evidence Trace/ })).toHaveTextContent(
      "Evidence Trace · 20 rows · 3 source artifacts",
    );
    expect(screen.queryByRole("list", { name: "Ledger rows" })).toBeNull();
  });

  it("renders every event type present in the ledger, with quote beside statement", () => {
    render(<EvidenceTraceView events={trace.events} defaultOpen />);
    expect(screen.getAllByTestId("trace-row-ARTIFACT_STORED")).toHaveLength(3);
    expect(screen.getAllByTestId("trace-row-EVIDENCE_ACCEPTED").length).toBeGreaterThanOrEqual(8);
    expect(screen.getByTestId("trace-row-ARTIFACT_NOT_PUBLISHED")).toHaveTextContent("NOT_PUBLISHED");
    expect(screen.getAllByTestId("trace-row-NO_MATERIAL_DELTA").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByTestId("trace-row-DELTA_PROPOSED")).toBeInTheDocument();
    const staged = screen.getByTestId("trace-row-DELTA_STAGED");
    expect(staged).toHaveAttribute("data-human-step", "true");
    expect(staged).toHaveAccessibleName(/Human decision required/);
    expect(within(staged).getByTestId("human-step-note")).toHaveTextContent("No external action happens without a human approval");

    // Slice 4 rows (MOO-705): approval chain is visible, human steps marked, refusals are gaps.
    expect(screen.getByTestId("trace-row-INQUIRY_STAGED")).toHaveAttribute("data-human-step", "true");
    expect(screen.getByTestId("trace-row-INQUIRY_APPROVAL_ISSUED")).toHaveAttribute("data-human-step", "true");
    expect(screen.getByTestId("trace-row-PACKET_RENDERED")).toHaveTextContent("DRAFT packet rendered");
    const refused = screen.getByTestId("trace-row-APPROVAL_REFUSED");
    expect(refused).toHaveTextContent("Approval refused — failed closed");
    expect(refused).toHaveTextContent("you approved different bytes than are staged");

    const capital = screen.getAllByTestId("trace-row-EVIDENCE_ACCEPTED").find((row) =>
      row.textContent?.includes("TOTAL Capital Project Costs $700,000"),
    );
    expect(capital).toBeDefined();
    const pair = within(capital as HTMLElement).getByTestId("quote-vs-statement");
    expect(within(pair).getByRole("blockquote")).toHaveTextContent("$700,000");
    expect(pair).toHaveTextContent("Neutral statement");
    expect(within(capital as HTMLElement).getByRole("button", { name: /tid121-project-plan-2024 at page 5/ })).toBeInTheDocument();
  });

  it("anchor click emits a jump event with artifact id and page", () => {
    render(<EvidenceTraceView events={trace.events} defaultOpen />);
    const handler = vi.fn();
    window.addEventListener(ARTIFACT_JUMP_EVENT, (event) => handler((event as CustomEvent).detail));
    fireEvent.click(screen.getAllByRole("button", { name: /tid121-amendment-1-2026 at page 3/ })[0]);
    expect(handler).toHaveBeenCalledWith({ artifactId: "tid121-amendment-1-2026", page: 3, span: null });
  });

  it("a delta chip focus opens the trace and highlights the matching evidence row", () => {
    render(<EvidenceTraceView events={trace.events} />);
    window.requestAnimationFrame = (cb) => (cb(0), 0);
    Element.prototype.scrollIntoView = vi.fn();
    act(() => focusEvidence("ev-tid121-amend1-capital-costs"));
    const row = document.querySelector('[data-evidence-id="ev-tid121-amend1-capital-costs"]');
    expect(row).not.toBeNull();
    expect(row?.className).toMatch(/ring-2/);
  });
});
