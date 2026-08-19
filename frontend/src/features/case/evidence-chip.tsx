"use client";

import { focusEvidence } from "@/features/case/evidence-focus";

/** Click → asks the Evidence Trace (MOO-698) to scroll to and highlight that row. */
export function EvidenceChip({ evidenceId }: { evidenceId: string }) {
  return (
    <button
      type="button"
      onClick={() => focusEvidence(evidenceId)}
      className="rounded-md border bg-muted px-2 py-0.5 font-mono text-xs hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring"
      aria-label={`Show evidence ${evidenceId} in the Evidence Trace`}
    >
      {evidenceId}
    </button>
  );
}
