"use client";

import { useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiErrorState } from "@/components/layout/api-error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { EvidenceChip } from "@/features/case/evidence-chip";
import { APPROVAL_COPY as COPY } from "@/features/approval/copy";
import { useApproveInquiry, useRejectInquiry, useStagedInquiry } from "@/features/approval/queries";
import type { InquiryStagedView } from "@/lib/api-types";

const inputClassName =
  "w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-ring";

export function ApprovalDrawer({ caseId }: { caseId: string }) {
  const query = useStagedInquiry(caseId);
  if (query.isPending) return <Skeleton role="status" className="h-24 w-full" aria-label="Loading approval state" />;
  if (query.isError) return <ApiErrorState error={query.error} what="the staged question" />;
  if (query.data === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{COPY.noInquiryTitle}</CardTitle>
          <CardDescription>{COPY.noInquiryDetail}</CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return <StagedInquiryCard caseId={caseId} staged={query.data} />;
}

function StagedInquiryCard({ caseId, staged }: { caseId: string; staged: InquiryStagedView }) {
  const [reviewerName, setReviewerName] = useState("");
  const [note, setNote] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);
  const approve = useApproveInquiry(caseId);
  const reject = useRejectInquiry(caseId);
  const proposal = staged.proposal;
  const busy = approve.isPending || reject.isPending;

  const onApprove = () => {
    if (!reviewerName.trim()) return setValidationMessage(COPY.needName);
    setValidationMessage(null);
    approve.mutate({ reviewer_name: reviewerName.trim(), artifact_hash: staged.artifact_hash });
  };
  const onReject = () => {
    if (!reviewerName.trim()) return setValidationMessage(COPY.needName);
    if (!note.trim()) return setValidationMessage(COPY.needNote);
    setValidationMessage(null);
    reject.mutate({ reviewer_name: reviewerName.trim(), note: note.trim() });
  };

  return (
    <Card data-testid="approval-drawer">
      <CardHeader>
        <CardTitle>{COPY.drawerTitle}</CardTitle>
        <CardDescription>{COPY.drawerDetail}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <section aria-label={COPY.question}>
          <h3 className="font-medium">{COPY.question}</h3>
          <p className="mt-1" data-testid="staged-question">{proposal.proposed_question}</p>
        </section>
        <section aria-label={COPY.scope}>
          <h3 className="font-medium">{COPY.scope}</h3>
          <p className="mt-1 text-muted-foreground">{proposal.scope_rationale}</p>
          <p className="mt-1 text-muted-foreground">
            {COPY.target}: {proposal.target_record_or_source}
          </p>
        </section>
        <section aria-label={COPY.citedEvidence}>
          <h3 className="font-medium">{COPY.citedEvidence}</h3>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {proposal.supporting_evidence_ids.map((evidenceId) => (
              <EvidenceChip key={evidenceId} evidenceId={evidenceId} />
            ))}
          </div>
        </section>
        <section aria-label={COPY.excluded}>
          <h3 className="font-medium">{COPY.excluded}</h3>
          <ul className="mt-1 list-disc pl-5 text-muted-foreground">
            {proposal.excluded_requests.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
        <section aria-label={COPY.hashLabel} className="rounded-md border bg-muted/40 p-3">
          <h3 className="font-medium">{COPY.hashLabel}</h3>
          <p className="mt-1 break-all font-mono text-xs" data-testid="proposal-hash">
            {staged.artifact_hash}
          </p>
          <p className="mt-1 text-muted-foreground">{COPY.hashDetail}</p>
          <p className="text-muted-foreground">{COPY.ttl(staged.ttl_minutes)}</p>
        </section>

        {approve.isSuccess ? (
          <Alert data-testid="approval-approved">
            <AlertTitle>{COPY.approvedTitle}</AlertTitle>
            <AlertDescription className="space-y-1">
              <p>{COPY.approvedDetail}</p>
              <p className="break-all font-mono text-xs">
                {COPY.tokenLabel}: {approve.data.token_id}
              </p>
              <p>
                {COPY.expiresLabel}: {new Date(approve.data.expires_at).toLocaleTimeString()}
              </p>
            </AlertDescription>
          </Alert>
        ) : reject.isSuccess ? (
          <Alert data-testid="approval-rejected">
            <AlertTitle>{COPY.rejectedTitle}</AlertTitle>
            <AlertDescription>{COPY.rejectedDetail}</AlertDescription>
          </Alert>
        ) : (
          <ApprovalActions
            reviewerName={reviewerName}
            note={note}
            busy={busy}
            onReviewerName={setReviewerName}
            onNote={setNote}
            onApprove={onApprove}
            onReject={onReject}
          />
        )}

        {validationMessage ? (
          <p role="alert" className="text-destructive">{validationMessage}</p>
        ) : null}
        {approve.isError ? (
          <Alert variant="destructive" data-testid="approval-refused">
            <AlertTitle>{COPY.refusedTitle}</AlertTitle>
            <AlertDescription>
              <p>{approve.error.message}</p>
              <p>{COPY.refusedDetail}</p>
            </AlertDescription>
          </Alert>
        ) : null}
        {reject.isError ? <ApiErrorState error={reject.error} what="the rejection" /> : null}
      </CardContent>
    </Card>
  );
}

function ApprovalActions(props: {
  reviewerName: string;
  note: string;
  busy: boolean;
  onReviewerName: (value: string) => void;
  onNote: (value: string) => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <div className="space-y-2">
      <label className="block">
        <span className="font-medium">{COPY.reviewerLabel}</span>
        <input
          type="text"
          value={props.reviewerName}
          onChange={(event) => props.onReviewerName(event.target.value)}
          className={`mt-1 ${inputClassName}`}
          disabled={props.busy}
        />
      </label>
      <p className="text-xs text-muted-foreground">{COPY.reviewerHonesty}</p>
      <label className="block">
        <span className="font-medium">{COPY.noteLabel}</span>
        <input
          type="text"
          value={props.note}
          onChange={(event) => props.onNote(event.target.value)}
          className={`mt-1 ${inputClassName}`}
          disabled={props.busy}
        />
      </label>
      <div className="flex gap-2 pt-1">
        <Button onClick={props.onApprove} disabled={props.busy} data-testid="approve-button">
          {props.busy ? COPY.approving : COPY.approveButton}
        </Button>
        <Button
          variant="outline"
          onClick={props.onReject}
          disabled={props.busy}
          data-testid="reject-button"
        >
          {COPY.rejectButton}
        </Button>
      </div>
    </div>
  );
}
