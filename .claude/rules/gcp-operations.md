# Google Cloud Operations Rules

Apply these rules whenever planning, implementing, reviewing, deploying, or debugging CivicTrace on Google Cloud.

## Model and Retrieval Cost

- Use Gemini Flash by default for extraction, classification, linking, comparison, and draft generation.
- Do not use a more expensive model unless a versioned evaluation fixture demonstrates that Flash fails a defined quality threshold and the change records a cost/quality rationale.
- Never send an entire public corpus to a model. Filter by source, date, entity, place, case, or dataset row in BigQuery/Firestore before an ADK agent receives a bounded evidence package.
- Cache artifact hashes, parsing outputs, and retrieval results. Process only changed source versions.
- Log model ID, prompt/schema version, job class, latency, and available usage metrics. Do not log raw restricted data.

## Cloud Run and Background Work

- Every non-exempt Cloud Run service uses minimum instances of zero and a finite maximum instance cap.
- Begin with the lowest viable CPU and memory allocation. Any increase must be documented in the infrastructure change.
- Separate `civictrace-api` from `civictrace-worker`; the worker is IAM-authenticated and not browser-accessible.
- Put long-running/retried work in Cloud Tasks. Use bounded task concurrency, finite retry attempts, and stable idempotency keys.
- Use Pub/Sub for event fan-out. Do not perform heavy ingestion or agent execution synchronously during source-event receipt.
- Use Cloud Scheduler only for defined adapter schedules. Disable schedules after the demo when monitoring is no longer needed.

## Storage, State, and Lifecycle

- Cloud Storage is the immutable raw-source vault. Every artifact must retain canonical URL, retrieval time, source ID, content hash, and lifecycle policy.
- Firestore stores cases, source events, evidence pointers, jobs, approvals, corrections, and audit ledger events—not large raw documents/media.
- BigQuery stores selected high-volume structured public records and supports filtering before inference.
- All temporary execution artifacts, media copies, failed-parsing outputs, and demo datasets require documented retention/lifecycle behavior in IaC.

## Security and Identity

- Use least-privilege service accounts. Do not grant project Owner, Editor, Storage Admin, or Billing Admin to application workers.
- Store third-party API keys and secret values in Secret Manager. Never commit a real key, service-account JSON, `.env`, transcript, or generated local cache.
- Authenticate internal service-to-service requests with Cloud Run IAM/service identity. Protect browser/API routes with an appropriate user-auth mechanism.
- Validate all webhook signatures, event IDs, payload schema, and replay/idempotency behavior.
- Source adapters may retrieve only allowlisted public domains and must respect source terms/rate limits. Do not automate sign-in, private browsing, form submission, or anti-bot bypass.

## Budget, Deployment, and Teardown

- Configure a billing budget and alerts before substantial deployment. Document thresholds and alert recipients in `docs/runbooks/cost-security-and-claude-code.md`.
- Treat budget alerts as warnings; enforce actual cost control through instance caps, queue concurrency, quotas, model selection, and source corpus limits.
- Infrastructure belongs in `infra/`. Do not make console-only changes without recording them in IaC or a documented temporary exception.
- Before deployment, run the guardrail verification script and review the output.
- Before destructive cleanup, show the target project, environment, region, and labeled resource list. Require explicit human confirmation.
- After the demo/submission proof is safely captured, disable schedules, drain or discard defined queues, scale services to zero, and remove disposable environment-labeled resources according to the teardown runbook.
