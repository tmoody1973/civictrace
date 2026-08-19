import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { CATEGORY_COPY, NOT_AVAILABLE, REVIEW_OUTCOME_COPY, SECTION_COPY } from "@/features/case/copy";
import { EvidenceChip } from "@/features/case/evidence-chip";
import type { LatestDeltaView } from "@/lib/api-types";

/** Rendered only from validated ledger fields. Every missing piece says so, in words. */
export function DecisionDeltaHeader({ delta }: { delta: LatestDeltaView | null }) {
  return (
    <Card data-testid="decision-delta">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">{SECTION_COPY.decisionDelta}</CardTitle>
        {delta ? (
          <>
            <p className="text-base font-semibold" data-testid="delta-category">
              {CATEGORY_COPY[delta.category]}
            </p>
            <CardDescription data-testid="delta-review-outcome">
              {delta.review_outcome ? REVIEW_OUTCOME_COPY[delta.review_outcome] : `Reviewer: ${NOT_AVAILABLE}`}
              {delta.requires_human_review ? ` · ${SECTION_COPY.humanReviewRequired}` : ""}
            </CardDescription>
          </>
        ) : (
          <CardDescription data-testid="delta-empty">{SECTION_COPY.noDelta}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <Section title={SECTION_COPY.summary}>
          <Text value={delta?.neutral_summary ?? null} testId="delta-summary" />
        </Section>
        <Section title={SECTION_COPY.established}>
          <List items={delta?.what_is_established ?? null} testId="delta-established" />
        </Section>
        <Section title={SECTION_COPY.notEstablished}>
          <List items={delta?.what_is_not_established ?? null} testId="delta-not-established" />
        </Section>
        <Section title={SECTION_COPY.nextEvidence}>
          <Text value={delta?.next_evidence_needed ?? null} testId="delta-next-evidence" />
        </Section>
        <Section title={SECTION_COPY.limitations}>
          <List items={delta?.limitations ?? null} testId="delta-limitations" />
        </Section>
        <Section title={SECTION_COPY.blockingIssues}>
          <List items={delta?.blocking_issues ?? null} testId="delta-blocking" emptyText="None recorded" />
        </Section>
        <Separator />
        <Section title={SECTION_COPY.originalEvidence}>
          <Chips ids={delta?.original_evidence_ids ?? null} testId="delta-original-ids" />
        </Section>
        <Section title={SECTION_COPY.laterEvidence}>
          <Chips ids={delta?.later_evidence_ids ?? null} testId="delta-later-ids" />
        </Section>
      </CardContent>
    </Card>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section aria-label={title} className="space-y-1">
      <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</h3>
      {children}
    </section>
  );
}

function Text({ value, testId }: { value: string | null; testId: string }) {
  return (
    <p data-testid={testId} className={value ? "leading-relaxed" : "italic text-muted-foreground"}>
      {value ?? NOT_AVAILABLE}
    </p>
  );
}

function List({ items, testId, emptyText }: { items: string[] | null; testId: string; emptyText?: string }) {
  if (items === null) return <Text value={null} testId={testId} />;
  if (items.length === 0) return <Text value={emptyText ?? null} testId={testId} />;
  return (
    <ul data-testid={testId} className="list-disc space-y-1 pl-5">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

function Chips({ ids, testId }: { ids: string[] | null; testId: string }) {
  if (ids === null || ids.length === 0) return <Text value={null} testId={testId} />;
  return (
    <div data-testid={testId} className="flex flex-wrap gap-1.5">
      {ids.map((id) => (
        <EvidenceChip key={id} evidenceId={id} />
      ))}
    </div>
  );
}
