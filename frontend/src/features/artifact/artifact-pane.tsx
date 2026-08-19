"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

import { ApiErrorState } from "@/components/layout/api-error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ArtifactHeader, type ArtifactLedgerInfo } from "@/features/artifact/artifact-header";
import { useArtifactFile } from "@/features/artifact/use-artifact-file";
import { useCaseTrace } from "@/features/case/queries";
import { onArtifactJump } from "@/features/trace/artifact-jump";
import type { TraceEventView } from "@/lib/api-types";

// pdf.js touches window/DOM APIs; render the viewer on the client only.
const PdfViewer = dynamic(() => import("@/features/artifact/pdf-viewer").then((m) => m.PdfViewer), {
  ssr: false,
  loading: () => <Skeleton role="status" className="h-64 w-full" aria-label="Loading PDF viewer" />,
});

type Selection = { artifactId: string; page: number | null };

export function ArtifactPane({ caseId }: { caseId: string }) {
  const trace = useCaseTrace(caseId);
  const [selection, setSelection] = useState<Selection | null>(null);

  useEffect(() => onArtifactJump(({ artifactId, page }) => setSelection({ artifactId, page })), []);

  const stored = (trace.data?.events ?? []).filter((event) => event.event_type === "ARTIFACT_STORED");
  const current = selection ?? (stored[0] ? { artifactId: stored[0].artifact_id, page: null } : null);
  const info = current ? ledgerInfoFor(current.artifactId, stored) : null;

  if (trace.isPending) return <Skeleton role="status" className="h-24 w-full" aria-label="Loading case records" />;
  if (trace.isError) return <ApiErrorState error={trace.error} what="the case records" />;
  if (!current || !info) return <p className="text-sm text-muted-foreground">No preserved document in this case yet.</p>;
  return <ArtifactView key={current.artifactId} selection={current} info={info} />;
}

function ArtifactView({ selection, info }: { selection: Selection; info: ArtifactLedgerInfo }) {
  const file = useArtifactFile(selection.artifactId);
  if (file.isPending) {
    return (
      <div className="space-y-3">
        <ArtifactHeader info={info} headerHash={null} computedHash={null} />
        <p className="text-sm text-muted-foreground" data-testid="artifact-loading">Fetching the saved copy…</p>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (file.isError) {
    return (
      <div className="space-y-3">
        <ArtifactHeader info={info} headerHash={null} computedHash={null} />
        <ApiErrorState error={file.error} what={`document ${selection.artifactId}`} />
      </div>
    );
  }
  const { bytes, mimeType, headerHash, computedHash } = file.data;
  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <ArtifactHeader info={info} headerHash={headerHash} computedHash={computedHash} />
      {mimeType === "application/pdf" ? (
        <PdfViewer bytes={bytes} anchoredPage={selection.page} label={selection.artifactId} />
      ) : (
        <p className="text-sm" data-testid="non-pdf-state">
          This saved copy is <code>{mimeType}</code>, not a PDF. The viewer shows PDFs only; open the official source link above
          to read it.
        </p>
      )}
    </div>
  );
}

function ledgerInfoFor(artifactId: string, stored: TraceEventView[]): ArtifactLedgerInfo {
  const row = stored.find((event) => event.artifact_id === artifactId);
  return {
    artifactId,
    canonicalUrl: row?.canonical_url ?? null,
    retrievedAt: row?.occurred_at ?? null,
    ledgerHash: row?.content_hash ?? null,
  };
}
