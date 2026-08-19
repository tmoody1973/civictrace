"use client";

import Link from "next/link";

import { Skeleton } from "@/components/ui/skeleton";
import { ApiErrorState } from "@/components/layout/api-error-state";
import { STATE_COPY } from "@/features/case/copy";
import { useCaseList } from "@/features/case/queries";

export function CaseRail({ activeCaseId }: { activeCaseId?: string }) {
  const query = useCaseList();
  if (query.isPending) return <Skeleton role="status" className="h-16 w-full" aria-label="Loading cases" />;
  if (query.isError) return <ApiErrorState error={query.error} what="the case list" />;
  if (query.data.length === 0) return <p className="text-sm text-muted-foreground">No cases in this ledger.</p>;
  return (
    <nav aria-label="Cases">
      <ul className="space-y-1">
        {query.data.map((item) => (
          <li key={item.case_id}>
            <Link
              href={`/cases/${encodeURIComponent(item.case_id)}`}
              aria-current={item.case_id === activeCaseId ? "page" : undefined}
              className="block rounded-md px-2 py-1.5 text-sm hover:bg-accent aria-[current=page]:bg-accent"
            >
              <span className="block truncate font-medium">{item.case_topic || item.case_id}</span>
              <span className="block text-xs text-foreground/90">{STATE_COPY[item.state].label}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
