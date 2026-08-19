"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { ApiErrorState } from "@/components/layout/api-error-state";
import { useCaseSummary } from "@/features/case/queries";

/** MOO-695 placeholder: proves the pipe works by showing the raw validated state + counts.
 *  MOO-697 replaces this with the Promise Card / Decision Delta header. */
export function CaseSummaryRaw({ caseId }: { caseId: string }) {
  const query = useCaseSummary(caseId);
  if (query.isPending) return <Skeleton className="h-24 w-full" aria-label="Loading case summary" />;
  if (query.isError) return <ApiErrorState error={query.error} what="the case summary" />;
  const { state, counts, case_topic } = query.data;
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
      <dt className="text-muted-foreground">Topic</dt>
      <dd>{case_topic || "—"}</dd>
      <dt className="text-muted-foreground">State</dt>
      <dd data-testid="case-state" className="font-mono">{state}</dd>
      {Object.entries(counts).map(([key, value]) => (
        <CountRow key={key} label={key} value={value} />
      ))}
    </dl>
  );
}

function CountRow({ label, value }: { label: string; value: number }) {
  return (
    <>
      <dt className="text-muted-foreground">{label.replaceAll("_", " ")}</dt>
      <dd data-testid={`count-${label}`} className="tabular-nums">{value}</dd>
    </>
  );
}
