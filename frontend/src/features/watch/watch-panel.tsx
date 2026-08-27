"use client";

import { Radar } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { WATCH_COPY } from "@/features/trace/copy";
import { api } from "@/lib/api";

const REFRESH_AFTER_RUN_MS = 20_000;

/** The honest watcher line: when the official record was last checked, and a gated
 * "check now" that enqueues ONE bounded worker run — results land in the trace. */
export function WatchPanel({ caseId }: { caseId: string }) {
  const client = useQueryClient();
  const status = useQuery({
    queryKey: ["cases", caseId, "watch"],
    queryFn: () => api.caseWatch(caseId),
    retry: false, // 503 just means the watcher is not enabled on this server
  });
  const run = useMutation({
    mutationFn: () => api.watchRun(),
    onSuccess: () => {
      // The worker needs a moment; then the trace and the checked-at line are fresh.
      setTimeout(() => {
        void client.invalidateQueries({ queryKey: ["cases", caseId, "watch"] });
        void client.invalidateQueries({ queryKey: ["cases", caseId, "trace"] });
        void client.invalidateQueries({ queryKey: ["case-trace", caseId] });
      }, REFRESH_AFTER_RUN_MS);
    },
  });

  if (status.isPending || status.isError) return null; // no watcher on this server: say nothing
  const targets = status.data.targets;
  const lastChecked = targets
    .map((target) => target.checked_at)
    .filter((value): value is string => value !== null)
    .sort()
    .at(-1);

  return (
    <section
      aria-label={WATCH_COPY.panelTitle}
      data-testid="watch-panel"
      className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-md border bg-muted/40 p-2 text-xs"
    >
      <span className="inline-flex items-center gap-1 font-medium">
        <Radar aria-hidden="true" className="size-3.5" />
        {WATCH_COPY.panelTitle}
      </span>
      {targets.length > 0 ? <span>{WATCH_COPY.watchedMatters(targets.length)}</span> : null}
      <span className="text-muted-foreground">
        {lastChecked
          ? WATCH_COPY.lastChecked(new Date(lastChecked).toLocaleString())
          : WATCH_COPY.neverChecked}
      </span>
      <Button
        size="sm"
        variant="outline"
        className="h-6 px-2 text-xs"
        disabled={run.isPending || run.isSuccess}
        onClick={() => run.mutate()}
      >
        {run.isPending ? WATCH_COPY.checking : WATCH_COPY.checkNow}
      </Button>
      {run.isSuccess ? <span className="text-muted-foreground">{WATCH_COPY.checkQueued}</span> : null}
    </section>
  );
}
