# CivicTrace Infrastructure

Infrastructure must be created and changed through this directory, using one chosen infrastructure-as-code tool. For the hackathon, choose **Terraform or Pulumi—do not introduce both.**

## Required Infrastructure Before Demo Deployment

| Resource | Purpose | Required guardrails |
|---|---|---|
| Cloud Run `civictrace-api` | Authenticated editor/Evidence Studio API. | Minimum instances 0, finite maximum instances, no browser-held AI keys. |
| Cloud Run `civictrace-worker` | Internal worker for Cloud Tasks, source ingestion, ADK jobs, and artifact rendering. | IAM-only invocation, minimum instances 0, finite maximum instances, dedicated least-privilege service account. |
| Cloud Storage buckets | Raw immutable artifacts, temporary execution artifacts, generated packets. | Lifecycle/retention rules, source provenance metadata, least privilege. |
| Firestore | Case/evidence/job/approval ledger. | Environment separation, documented indexes, least-privilege access. |
| Pub/Sub topics | Source/event fan-out. | Schema/labels where applicable; no direct browser publishing. |
| Cloud Tasks queues | Idempotent retried work. | Finite concurrency and retry limits; worker IAM target. |
| Cloud Scheduler | Controlled source polling. | Named schedules, environment labels, disabled after demo when appropriate. |
| BigQuery datasets | Selected structured corpus/backfill. | Region, expiration/retention, project labels, limited service identity. |
| Secret Manager | Third-party API keys/config secrets if later approved. | No secret values in Git or Terraform state. |
| IAM service accounts | API, worker, deployment identities. | Least privilege; no broad owner/editor roles. |
| Budget / alerts | Human notification on spend. | Document threshold/recipients; pair with resource caps. |

## Environment Labels

Every resource must be labeled at least with:

```text
app=civictrace
environment=dev|demo
owner=replace-with-team-or-person
managed-by=terraform|pulumi
teardown=required|retain
```

## Implementation Order

Start with `dev` only. Create a minimal service and verify IAM, logs, and scale-to-zero before adding queues, datasets, or scheduled source monitoring. The final `demo` environment should use the same reviewed modules with different variable values, not console-only configuration.
