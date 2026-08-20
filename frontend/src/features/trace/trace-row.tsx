"use client";

import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  CircleDashed,
  FileCheck2,
  FileText,
  FileX2,
  GitCompareArrows,
  HelpCircle,
  ShieldCheck,
  ShieldX,
  UserCheck,
  UserX,
} from "lucide-react";

import { ChainOfThoughtStep } from "@/components/ai-elements/chain-of-thought";
import { Badge } from "@/components/ui/badge";
import { CATEGORY_COPY, REVIEW_OUTCOME_COPY } from "@/features/case/copy";
import { EVIDENCE_STATUS_LABEL, TRACE_COPY } from "@/features/trace/copy";
import { EvidenceAnchorLink } from "@/features/trace/evidence-anchor-link";
import type { TraceRow } from "@/features/trace/row-model";
import type { LedgerEventType } from "@/lib/api-types";

const ICONS: Record<LedgerEventType, typeof CheckCircle2> = {
  ARTIFACT_STORED: FileCheck2,
  ARTIFACT_NOT_PUBLISHED: FileX2,
  EVIDENCE_ACCEPTED: CheckCircle2,
  EXTRACTION_REJECTED: Ban,
  NO_MATERIAL_DELTA: CircleDashed,
  DELTA_PROPOSED: GitCompareArrows,
  DELTA_REJECTED: Ban,
  DELTA_STAGED: UserCheck,
  CASE_HUMAN_REVIEW: AlertTriangle,
  INQUIRY_STAGED: HelpCircle,
  INQUIRY_REJECTED: Ban,
  INQUIRY_APPROVAL_ISSUED: ShieldCheck,
  INQUIRY_APPROVAL_REJECTED: UserX,
  APPROVAL_REFUSED: ShieldX,
  PACKET_RENDERED: FileText,
};

export function TraceRowView({ row, highlighted }: { row: TraceRow; highlighted: boolean }) {
  const { event } = row;
  return (
    <ChainOfThoughtStep
      id={`trace-row-${row.id}`}
      data-testid={`trace-row-${row.eventType}`}
      data-evidence-id={row.evidenceId ?? undefined}
      data-human-step={row.isHuman ? "true" : undefined}
      role="listitem"
      aria-label={row.isHuman ? `${TRACE_COPY.humanStep}: ${row.label}` : row.label}
      icon={ICONS[row.eventType]}
      status={row.stepStatus}
      label={
        <span className="flex flex-wrap items-center gap-2">
          <span className={row.isHuman ? "font-semibold text-foreground" : "font-medium"}>{row.label}</span>
          <Badge variant={row.isGap ? "destructive" : row.isHuman ? "default" : "outline"} className="font-mono text-[10px]">
            {row.status}
          </Badge>
          <time dateTime={row.occurredAt} className="text-xs text-muted-foreground">
            {new Date(row.occurredAt).toLocaleString()}
          </time>
        </span>
      }
      className={highlighted ? "rounded-md bg-accent/60 ring-2 ring-ring p-2 -m-2" : undefined}
    >
      {event.event_type === "ARTIFACT_STORED" && (
        <Detail label={TRACE_COPY.hash}>
          <code className="break-all text-xs">{event.content_hash}</code>
          <div className="mt-1">
            <EvidenceAnchorLink artifactId={row.artifactId} anchor={null} canonicalUrl={row.canonicalUrl} />
          </div>
        </Detail>
      )}
      {row.isGap && (
        <Detail label={TRACE_COPY.reason}>
          <p className="text-xs leading-relaxed">{event.reason ?? "No reason recorded."}</p>
        </Detail>
      )}
      {row.isHuman && event.reason && (
        <Detail label={TRACE_COPY.reason}>
          <p className="text-xs leading-relaxed">{event.reason}</p>
        </Detail>
      )}
      {event.proposed_question && (
        <Detail label={TRACE_COPY.proposedQuestion}>
          <p className="text-xs leading-relaxed">{event.proposed_question}</p>
        </Detail>
      )}
      {event.event_type === "EVIDENCE_ACCEPTED" && <EvidenceBody row={row} />}
      {(event.event_type === "NO_MATERIAL_DELTA" || event.event_type === "DELTA_REJECTED") && event.reason && !row.isGap && (
        <Detail label={TRACE_COPY.reason}>
          <p className="text-xs">{event.reason}</p>
        </Detail>
      )}
      {(event.event_type === "DELTA_PROPOSED" ||
        event.event_type === "DELTA_STAGED" ||
        event.event_type === "CASE_HUMAN_REVIEW" ||
        event.event_type === "DELTA_REJECTED") &&
        event.category && <DeltaBody row={row} />}
      {row.isHuman && (
        <p className="text-xs text-foreground" data-testid="human-step-note">
          {TRACE_COPY.humanStepDetail}
        </p>
      )}
    </ChainOfThoughtStep>
  );
}

function EvidenceBody({ row }: { row: TraceRow }) {
  const { event } = row;
  const anchor = event.anchors[0] ?? null;
  return (
    <div className="space-y-2">
      <div className="grid gap-3 md:grid-cols-2" data-testid="quote-vs-statement">
        <Detail label={TRACE_COPY.quote}>
          <blockquote className="border-l-2 pl-2 font-mono text-xs leading-relaxed">{event.verbatim_excerpt}</blockquote>
        </Detail>
        <Detail label={TRACE_COPY.statement}>
          <p className="text-xs leading-relaxed">{event.neutral_statement}</p>
        </Detail>
      </div>
      <Detail label={TRACE_COPY.anchors}>
        <div className="flex flex-wrap items-center gap-2">
          <EvidenceAnchorLink artifactId={row.artifactId} anchor={anchor} canonicalUrl={row.canonicalUrl} />
          <span className="text-xs text-muted-foreground">{EVIDENCE_STATUS_LABEL[event.status] ?? event.status}</span>
          {event.evidence_id ? <code className="text-[10px] text-muted-foreground">{event.evidence_id}</code> : null}
        </div>
      </Detail>
      {event.limitations.length > 0 && (
        <Detail label={TRACE_COPY.limitations}>
          <ul className="list-disc pl-4 text-xs">
            {event.limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Detail>
      )}
    </div>
  );
}

function DeltaBody({ row }: { row: TraceRow }) {
  const { event } = row;
  return (
    <div className="space-y-2 text-xs">
      {event.category ? <p className="font-medium">{CATEGORY_COPY[event.category]}</p> : null}
      {event.neutral_summary ? <p className="leading-relaxed">{event.neutral_summary}</p> : null}
      <div className="grid gap-3 md:grid-cols-2">
        <ListDetail label={TRACE_COPY.established} items={event.what_is_established} />
        <ListDetail label={TRACE_COPY.notEstablished} items={event.what_is_not_established} />
      </div>
      {event.next_evidence_needed ? <Detail label={TRACE_COPY.nextEvidence}><p>{event.next_evidence_needed}</p></Detail> : null}
      {event.review_outcome ? <p>{REVIEW_OUTCOME_COPY[event.review_outcome]}</p> : null}
      <ListDetail label={TRACE_COPY.blockingIssues} items={event.blocking_issues} />
      <ListDetail label={TRACE_COPY.reviewNotes} items={event.review_notes} />
    </div>
  );
}

function Detail({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      {children}
    </div>
  );
}

function ListDetail({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <Detail label={label}>
      <ul className="list-disc pl-4">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </Detail>
  );
}
