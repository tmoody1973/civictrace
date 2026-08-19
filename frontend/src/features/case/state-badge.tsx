import { AlertTriangle, CheckCircle2, Hourglass } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { STATE_COPY } from "@/features/case/copy";
import type { CaseState } from "@/lib/api-types";

const ICONS: Record<CaseState, typeof CheckCircle2> = {
  NO_DELTA: CheckCircle2,
  DELTA_STAGED: Hourglass,
  HUMAN_REVIEW: AlertTriangle,
};

/** Words + icon, never color alone. */
export function StateBadge({ state }: { state: CaseState }) {
  const Icon = ICONS[state];
  return (
    <Badge variant="outline" data-state={state} data-testid="state-badge" className="gap-1.5 py-1 text-sm font-medium">
      <Icon aria-hidden="true" className="size-4" />
      {STATE_COPY[state].label}
    </Badge>
  );
}
