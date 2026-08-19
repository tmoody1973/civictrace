"use client";

import { ExternalLink, FileText } from "lucide-react";

import { jumpToArtifact } from "@/features/trace/artifact-jump";
import { TRACE_COPY } from "@/features/trace/copy";
import type { AnchorView } from "@/lib/api-types";

/** One click from any anchor to the real page (PDF pane, MOO-699) or the official source. */
export function EvidenceAnchorLink({
  artifactId,
  anchor,
  canonicalUrl,
}: {
  artifactId: string;
  anchor: AnchorView | null;
  canonicalUrl: string | null;
}) {
  const page = anchor?.anchor_type === "page" ? Number.parseInt(anchor.anchor_value, 10) : Number.NaN;
  const anchorText = anchor ? `${anchor.anchor_type.replaceAll("_", " ")} ${anchor.anchor_value}` : "whole document";
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5">
      <button
        type="button"
        data-testid="anchor-jump"
        onClick={() => jumpToArtifact({ artifactId, page: Number.isFinite(page) ? page : null })}
        aria-label={`Open ${artifactId} at ${anchorText}`}
        className="inline-flex items-center gap-1 rounded-md border bg-background px-2 py-0.5 font-mono text-xs text-foreground hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring"
      >
        <FileText aria-hidden="true" className="size-3" />
        {artifactId} · {anchorText}
      </button>
      {canonicalUrl ? (
        <a
          href={canonicalUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-foreground underline-offset-2 hover:underline"
          aria-label={`${TRACE_COPY.openSource} for ${artifactId} (new tab)`}
        >
          <ExternalLink aria-hidden="true" className="size-3" />
          {TRACE_COPY.openSource}
        </a>
      ) : null}
    </span>
  );
}
