"use client";

import { ApiErrorState } from "@/components/layout/api-error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { DecisionDeltaHeader } from "@/features/case/decision-delta-header";
import { PromiseCard } from "@/features/case/promise-card";
import { useCaseSummary } from "@/features/case/queries";

export function CaseReviewPane({ caseId }: { caseId: string }) {
  const query = useCaseSummary(caseId);
  if (query.isPending) return <Skeleton role="status" className="h-40 w-full" aria-label="Loading case" />;
  if (query.isError) return <ApiErrorState error={query.error} what="the case summary" />;
  return (
    <div className="space-y-4">
      <PromiseCard summary={query.data} />
      <DecisionDeltaHeader delta={query.data.latest_delta} />
    </div>
  );
}
