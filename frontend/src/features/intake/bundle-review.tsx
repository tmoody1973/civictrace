"use client";

import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { ApiErrorState } from "@/components/layout/api-error-state";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreationProgress, useIntakeApprove } from "@/features/intake/queries";
import type { CandidateBundleView } from "@/lib/api-types";

const inputClassName =
  "w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-ring";

type Role = "none" | "promise" | "later";

/** The human review: assign roles, state the topic, approve — or nothing happens. */
export function BundleReview({ bundle }: { bundle: CandidateBundleView }) {
  const [roles, setRoles] = useState<Record<number, Role>>({});
  const [topic, setTopic] = useState("");
  const [reviewer, setReviewer] = useState("");
  const approve = useIntakeApprove(bundle.bundle_id);

  const promiseIds = ids(roles, "promise");
  const laterIds = ids(roles, "later");
  const readyToApprove =
    bundle.status === "DRAFT" && promiseIds.length > 0 && topic.trim().length >= 10 && reviewer.trim();

  return (
    <Card data-testid="candidate-bundle">
      <CardHeader>
        <CardTitle className="text-base">
          File {bundle.legistar_file} — {bundle.title}
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          {bundle.matter_type ?? "Matter"} · status {bundle.matter_status ?? "unknown"} · introduced{" "}
          {bundle.intro_date ?? "unknown"} ·{" "}
          <a
            className="inline-flex items-center gap-1 underline underline-offset-2"
            href={bundle.matter_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink aria-hidden="true" className="size-3" />
            Official record
          </a>
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <StatusNotice bundle={bundle} />
        {bundle.status === "DRAFT" ? (
          <>
            <div className="rounded-md border bg-muted/40 p-3 text-sm">
              <p className="font-medium">How this works</p>
              <ol className="mt-1 list-decimal space-y-1 pl-5">
                <li>
                  Pick <strong>the promise</strong> — the document where the City commits to
                  something (money, housing, a project). Open each official source if you are
                  not sure; usually it is the plan or agreement.
                </li>
                <li>
                  Mark <strong>later evidence</strong> — documents that show follow-through,
                  cost, or an independent check (reports, review letters).
                </li>
                <li>
                  Say what to watch, sign your name, approve. The system then downloads those
                  exact documents from the City, fingerprints them so they can never silently
                  change, and builds the case. You review everything it finds before anything
                  leaves the system.
                </li>
              </ol>
              <p className="mt-1 text-muted-foreground">
                &ldquo;Not used&rdquo; keeps a document out of the case. You can always look the
                file up again and choose differently.
              </p>
            </div>
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">
                Which document states the promise? Which show what happened after?
              </legend>
              {bundle.attachments.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  The official record lists no document attachments for this file.
                </p>
              ) : null}
              {bundle.attachments.map((attachment) => (
                <div key={attachment.attachment_id} className="flex flex-wrap items-center gap-2 text-sm">
                  <select
                    aria-label={`Role for ${attachment.name}`}
                    className="rounded-md border bg-background px-2 py-1 text-sm disabled:opacity-60"
                    value={roles[attachment.attachment_id] ?? "none"}
                    disabled={!isPdf(attachment.url)}
                    onChange={(event) =>
                      setRoles((current) => ({
                        ...current,
                        [attachment.attachment_id]: event.target.value as Role,
                      }))
                    }
                  >
                    <option value="none">Not used</option>
                    <option value="promise">The promise — what the City committed to</option>
                    <option value="later">What happened after — follow-through or review</option>
                  </select>
                  <span>{attachment.name}</span>
                  {!isPdf(attachment.url) ? (
                    <Badge variant="outline">Word file — can&apos;t be used yet, PDFs only</Badge>
                  ) : null}
                  <a
                    className="inline-flex items-center gap-1 text-xs underline underline-offset-2"
                    href={attachment.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink aria-hidden="true" className="size-3" />
                    Open official source
                  </a>
                </div>
              ))}
            </fieldset>
            <label className="block text-sm">
              <span className="font-medium">What is this case about? (the case topic)</span>
              <textarea
                className={`mt-1 ${inputClassName}`}
                rows={2}
                value={topic}
                onChange={(event) => setTopic(event.target.value)}
                placeholder={`e.g. The City's commitment in file ${bundle.legistar_file} and what later public records show about follow-through`}
              />
            </label>
            <label className="block text-sm">
              <span className="font-medium">Your name (recorded as the reviewer)</span>
              <input
                className={`mt-1 ${inputClassName}`}
                value={reviewer}
                onChange={(event) => setReviewer(event.target.value)}
              />
            </label>
            <Button
              disabled={!readyToApprove || approve.isPending}
              onClick={() =>
                approve.mutate({
                  reviewer_name: reviewer.trim(),
                  case_topic: topic.trim(),
                  promise_attachment_ids: promiseIds,
                  later_attachment_ids: laterIds,
                })
              }
            >
              {approve.isPending ? "Approving…" : "Approve — create this case"}
            </Button>
            {!readyToApprove ? (
              <p className="text-sm text-muted-foreground">
                To approve: mark at least one promise document, write a topic (10+ characters),
                and sign your name.
              </p>
            ) : null}
            {approve.isError ? <ApiErrorState error={approve.error} what="the approval" /> : null}
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

function StatusNotice({ bundle }: { bundle: CandidateBundleView }) {
  if (bundle.status === "DRAFT") return null;
  if (bundle.status === "FAILED") {
    return (
      <Alert variant="destructive" role="alert">
        <AlertTitle>Case creation failed</AlertTitle>
        <AlertDescription>{bundle.failure_reason ?? "No reason recorded."}</AlertDescription>
      </Alert>
    );
  }
  if (bundle.status === "CASE_CREATED" && bundle.case_id) {
    return (
      <Alert>
        <AlertTitle>Case created</AlertTitle>
        <AlertDescription>
          The documents are fetched, hash-locked, and the evidence pipeline has run.{" "}
          <Link className="underline underline-offset-2" href={`/cases/${bundle.case_id}`}>
            Open the case in the Evidence Studio
          </Link>
        </AlertDescription>
      </Alert>
    );
  }
  return <CreationProgress bundle={bundle} />;
}

/** Live steps from the case record — observable workflow, never model "thinking". */
function CreationProgress({ bundle }: { bundle: CandidateBundleView }) {
  const caseId = `case-intake-${bundle.legistar_file}`;
  const progress = useCreationProgress(caseId, true);
  const events = progress.data?.events ?? [];
  const stored = events.filter((event) => event.event_type === "ARTIFACT_STORED");
  const evidence = events.filter((event) => event.event_type === "EVIDENCE_ACCEPTED");
  const compared = events.some((event) =>
    ["DELTA_PROPOSED", "DELTA_STAGED", "NO_MATERIAL_DELTA", "CASE_HUMAN_REVIEW"].includes(
      event.event_type,
    ),
  );
  return (
    <Alert data-testid="creation-progress">
      <AlertTitle>
        <Badge>{bundle.status}</Badge> Building the case — live steps
      </AlertTitle>
      <AlertDescription>
        <ul className="mt-1 list-disc space-y-1 pl-5">
          <li>Approved; documents requested from the City&apos;s servers ✓</li>
          {events.length === 0 ? (
            <li>Fetching the official documents and locking their fingerprints…</li>
          ) : null}
          {stored.map((event) => (
            <li key={event.event_id}>
              Saved the exact official copy of <code>{event.artifact_id}</code>, fingerprint
              recorded ✓
            </li>
          ))}
          {evidence.length > 0 ? (
            <li>
              {evidence.length} evidence excerpt{evidence.length === 1 ? "" : "s"} extracted —
              each one anchored to a page and checked against the document ✓
            </li>
          ) : stored.length > 0 ? (
            <li>Reading the documents for anchored evidence…</li>
          ) : null}
          {compared ? (
            <li>Promise compared with later records ✓ — finishing up</li>
          ) : evidence.length > 0 ? (
            <li>Comparing the promise with the later records…</li>
          ) : null}
        </ul>
        <p className="mt-2 text-muted-foreground">
          Every line above is a recorded step you can audit later in the case — this is the
          system&apos;s work log, not a narration. Updates by itself; about 2–4 minutes total.
        </p>
      </AlertDescription>
    </Alert>
  );
}

function isPdf(url: string): boolean {
  return url.toLowerCase().endsWith(".pdf");
}

function ids(roles: Record<number, Role>, role: Role): number[] {
  return Object.entries(roles)
    .filter(([, value]) => value === role)
    .map(([key]) => Number(key));
}
