import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { COUNT_COPY, SECTION_COPY, STATE_COPY } from "@/features/case/copy";
import { StateBadge } from "@/features/case/state-badge";
import type { CaseSummaryView } from "@/lib/api-types";

export function PromiseCard({ summary }: { summary: CaseSummaryView }) {
  return (
    <Card data-testid="promise-card">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">{SECTION_COPY.promiseCard}</CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          <StateBadge state={summary.state} />
          <span className="font-mono text-xs text-muted-foreground">{summary.state}</span>
        </div>
        <CardDescription>{STATE_COPY[summary.state].detail}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-relaxed" data-testid="case-topic">
          {summary.case_topic.trim() || "No topic recorded in the corpus manifest."}
        </p>
        <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 text-sm" aria-label="Case counts">
          {(Object.keys(COUNT_COPY) as Array<keyof typeof COUNT_COPY>).map((key) => (
            <div key={key} className="contents">
              <dt className="text-muted-foreground">{COUNT_COPY[key]}</dt>
              <dd className="tabular-nums" data-testid={`count-${key}`}>
                {summary.counts[key]}
              </dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}
