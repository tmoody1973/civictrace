# Deployment Runbook

## Purpose

Deploy a reviewed CivicTrace environment without bypassing source, evidence, privacy, cost, or approval safeguards.

## Preconditions

1. Read `CLAUDE.md`, `.claude/rules/gcp-operations.md`, `infra/README.md`, and the current source allowlist.
2. Confirm the target project ID, environment, region, and resource labels.
3. Confirm the replay corpus contains only reviewed public or synthetic non-sensitive fixtures.
4. Run source/agent evaluation suites, including grounding, missingness, conflict, idempotency, privacy, and approval-gate tests.
5. Run the cloud guardrail verification script once implemented.
6. Confirm budget alerts, service max-instance caps, Storage lifecycle rules, IAM service accounts, and Cloud Run endpoint authentication.
7. Review the IaC plan with a human. Do not use console-only configuration as the source of truth.

## Deployment Sequence

1. Apply baseline infrastructure through reviewed IaC.
2. Deploy `civictrace-worker`, then verify its IAM-only invocation and logs.
3. Deploy `civictrace-api`, then verify user authentication and no exposure of server secrets.
4. Verify Pub/Sub, Cloud Tasks, Firestore, Cloud Storage, and BigQuery permissions using a safe test event.
5. Run a known replay-corpus event end to end.
6. Verify the Decision Delta displays both original/later source anchors and no unsupported claim.
7. Verify duplicate-event suppression, missing-source handling, and approval denial behavior.
8. Capture Cloud Run/log/trace evidence required for the demo.

## Rollback

If evidence, approval, privacy, or identity checks fail, disable the relevant Scheduler job, pause the queue, roll back the application revision or IaC change, and preserve diagnostic records without exposing restricted data.
