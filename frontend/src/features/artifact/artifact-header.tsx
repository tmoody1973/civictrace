"use client";

import { Check, Copy, ExternalLink } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { compareHashes, HASH_VERDICT_COPY } from "@/features/artifact/hash";

export type ArtifactLedgerInfo = {
  artifactId: string;
  canonicalUrl: string | null;
  retrievedAt: string | null;
  ledgerHash: string | null;
};

export function ArtifactHeader({
  info,
  headerHash,
  computedHash,
}: {
  info: ArtifactLedgerInfo;
  headerHash: string | null;
  computedHash: string | null;
}) {
  const verdict = compareHashes(info.ledgerHash, headerHash, computedHash);
  const [copied, setCopied] = useState(false);
  const hash = info.ledgerHash ?? computedHash;
  return (
    <div className="space-y-1 text-xs" data-testid="artifact-header">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono font-medium">{info.artifactId}</span>
        {info.canonicalUrl ? (
          <a href={info.canonicalUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 underline-offset-2 hover:underline">
            <ExternalLink aria-hidden="true" className="size-3" /> Open official source
          </a>
        ) : null}
        {info.retrievedAt ? (
          <span className="text-muted-foreground">
            saved <time dateTime={info.retrievedAt}>{new Date(info.retrievedAt).toLocaleString()}</time>
          </span>
        ) : null}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <code className="break-all text-[11px]">{hash ?? "hash not available"}</code>
        {hash ? (
          <Button
            variant="ghost"
            size="sm"
            aria-label="Copy fingerprint"
            onClick={() => navigator.clipboard?.writeText(hash).then(() => setCopied(true))}
          >
            {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
          </Button>
        ) : null}
        <Badge variant={verdict === "match" ? "default" : verdict === "mismatch" ? "destructive" : "outline"} data-testid="hash-verdict" data-verdict={verdict}>
          {HASH_VERDICT_COPY[verdict]}
        </Badge>
      </div>
    </div>
  );
}
