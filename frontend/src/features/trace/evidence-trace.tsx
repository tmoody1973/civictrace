"use client";

import { useEffect, useState } from "react";

import { ChainOfThought, ChainOfThoughtContent, ChainOfThoughtHeader } from "@/components/ai-elements/chain-of-thought";
import { ApiErrorState } from "@/components/layout/api-error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { onEvidenceFocus } from "@/features/case/evidence-focus";
import { useCaseTrace } from "@/features/case/queries";
import { TRACE_COPY } from "@/features/trace/copy";
import { countArtifacts, toTraceRow } from "@/features/trace/row-model";
import { TraceRowView } from "@/features/trace/trace-row";
import type { TraceEventView } from "@/lib/api-types";

export function EvidenceTrace({ caseId }: { caseId: string }) {
  const query = useCaseTrace(caseId);
  if (query.isPending) return <Skeleton role="status" className="h-10 w-full" aria-label="Loading Evidence Trace" />;
  if (query.isError) return <ApiErrorState error={query.error} what="the Evidence Trace" />;
  return <EvidenceTraceView events={query.data.events} />;
}

/** Collapsed by default; opens on demand; a delta chip click opens it and highlights the row. */
export function EvidenceTraceView({ events, defaultOpen = false }: { events: TraceEventView[]; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const [focused, setFocused] = useState<string | null>(null);
  const rows = events.map(toTraceRow);

  useEffect(
    () =>
      onEvidenceFocus(({ evidenceId }) => {
        setOpen(true);
        setFocused(evidenceId);
        requestAnimationFrame(() => {
          document
            .querySelector(`[data-evidence-id="${CSS.escape(evidenceId)}"]`)
            ?.scrollIntoView({ behavior: "smooth", block: "center" });
        });
      }),
    [],
  );

  if (rows.length === 0) return <p className="text-sm text-muted-foreground">{TRACE_COPY.noRows}</p>;
  return (
    <ChainOfThought open={open} onOpenChange={setOpen} data-testid="evidence-trace">
      <ChainOfThoughtHeader aria-label="Toggle Evidence Trace">
        {TRACE_COPY.header(rows.length, countArtifacts(events))}
      </ChainOfThoughtHeader>
      <ChainOfThoughtContent>
        <div role="list" aria-label="Ledger rows" className="space-y-4">
          {rows.map((row) => (
            <TraceRowView key={row.id} row={row} highlighted={row.evidenceId !== null && row.evidenceId === focused} />
          ))}
        </div>
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
}
