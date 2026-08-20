"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiErrorState } from "@/components/layout/api-error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { APPROVAL_COPY as COPY } from "@/features/approval/copy";
import { usePacket } from "@/features/approval/queries";

/** The rendered DRAFT packet, shown verbatim. The markdown text IS the artifact; we do not
 *  restyle it into prose the ledger never saw. */
export function PacketView({ caseId }: { caseId: string }) {
  const query = usePacket(caseId);
  if (query.isPending) return <Skeleton role="status" className="h-24 w-full" aria-label="Loading packet state" />;
  if (query.isError) return <ApiErrorState error={query.error} what="the packet" />;
  if (query.data === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{COPY.noPacketTitle}</CardTitle>
          <CardDescription>{COPY.noPacketDetail}</CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return (
    <Card data-testid="packet-view">
      <CardHeader>
        <CardTitle>{COPY.packetTitle}</CardTitle>
        <CardDescription>
          <span
            className="inline-block rounded-md border border-amber-500/60 bg-amber-500/10 px-2 py-0.5 font-medium text-foreground"
            data-testid="draft-banner"
          >
            {COPY.packetBanner}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div>
          <h3 className="font-medium">{COPY.packetHashLabel}</h3>
          <p className="break-all font-mono text-xs" data-testid="packet-hash">
            {query.data.packet_hash}
          </p>
        </div>
        <pre
          tabIndex={0}
          aria-label="Rendered packet markdown"
          className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md border bg-muted/40 p-3 font-mono text-xs"
        >
          {query.data.markdown}
        </pre>
      </CardContent>
    </Card>
  );
}
