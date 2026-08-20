# Slice 5 — Cloud deploy (dev), planned for Linear

## Context

Slices 1–4 are done: the whole loop runs locally — record → evidence → delta → question → human approval → DRAFT packet, with refusals on screen and in the ledger. The MVP definition of done (CLAUDE.md §8) needs the same loop running **in a deployed Google Cloud environment**: raw artifacts preserved in Cloud Storage, ledger in Firestore, duplicate handled once, missing report explicit, a failed approval demo, and job/trace lineage visible in the Console. Slice 5 builds that, in Terraform, on the existing `civictrace-dev-tm` project ($10/month budget already set, MOO-690).

**Tarik's three calls (2026-08-20):** local UI talking to the cloud API; **BigQuery in** with a minimal dataset; **public API URL guarded by a bearer token** from Secret Manager (worker stays IAM-only).

## Ground rules carried into every issue

- IaC only: **Terraform** in `infra/terraform` (one tool, per `infra/README.md`). No console-only changes.
- Every resource labeled `app=civictrace, environment=dev, owner=tarik, managed-by=terraform, teardown=required`.
- Cloud Run: min instances **0**, finite max (2), least-privilege service accounts, no browser-held AI keys.
- Gemini Flash only, and only for the Document Evidence role (same `RoleRoutingRunner` as local); delta/reviewer/planner stay fixtures. Cost stays cents.
- **Human confirmation before every `terraform apply`, deploy, or destroy** — I prepare and show the plan output; Tarik says go.
- Existing DI seams get cloud implementations; the fake-backed test suite stays green with no credentials.

## The six issues (Linear project "CivicTrace — Slice 5: Cloud deploy (dev)")

1. **5.1 Terraform baseline + guardrail script** — providers/backend, APIs, labels; GCS buckets (immutable `vault` + `packets`, lifecycle rules); Firestore (native); service accounts (`api`, `worker`, `deploy`); Secret Manager secret for the API bearer token (value set by Tarik, never in Git/state); `infra/scripts/verify-guardrails.sh` (checks min-0/max caps, labels, IAM-only worker, budget exists) + `cost-status.sh`. No services yet. *Apply gate: Tarik.*
2. **5.2 Firestore ledger + GCS vault behind the existing seams** — `FirestoreLedger` (CaseRepository protocol, `app/repositories/cases.py` shape; data model per stack-decision doc §5) and `GcsArtifactVault` (ArtifactVault protocol, hash/provenance-first like `LocalFixtureVault`). Tests against the Firestore emulator + GCS fake; idempotent event ids unchanged. Pure code, no apply gate.
3. **5.3 Services + queues** — Dockerfile; Cloud Run `civictrace-worker` (IAM-only; Cloud Tasks target endpoint that runs one source event through the workflow) and `civictrace-api` (existing FastAPI + bearer-token middleware; public URL); Pub/Sub topic `source.events` → push to a Tasks-enqueue endpoint; Tasks queue (finite concurrency/retries, idempotency keys from existing `SourceJobKeys`). Vertex via worker service identity. *Apply + deploy gate: Tarik.*
4. **5.4 BigQuery minimal + cloud replay end to end** — dataset `civictrace_dev` with one table of corpus-manifest rows, loaded by script and queried once in the replay path as the prefilter step (honest use, not decoration); then publish the 4 source events → Pub/Sub → Tasks → worker → Firestore/GCS. Verify in the cloud: DELTA_STAGED, INQUIRY_STAGED, duplicate suppressed, NOT_PUBLISHED row, approval refusal fail-closed. Capture Console/log proof (`docs/hackathon/proof/`). *Apply gate: Tarik.*
5. **5.5 Studio against the cloud API** — local UI pointed at the public API URL with the bearer token in local env (never committed); approve → packet rendered to the packets bucket; screenshots + demo-script updates (Console lineage beat). No new infra.
6. **5.6 Teardown + cost proof** — implement the teardown runbook as `infra/scripts/` automation that fails closed on label/project mismatch; run `cost-status.sh`; scale-to-zero verified; document what stays vs goes. *Destroy gate: Tarik, per runbook ("the owner makes that decision").*

Also: `docs/decisions/004` — the three calls above (UI local, BQ minimal-in, public+bearer), each with what we traded; "What actually happened" left blank for Tarik.

## Verification (proves the DoD)

- `verify-guardrails.sh` output clean before each deploy.
- Cloud replay run: Firestore ledger shows the same event chain as local; GCS holds the 3 PDFs with hashes + the rendered packet; Tasks/Pub/Sub metrics visible; one duplicate suppressed; `tid-annual-report-2025` NOT_PUBLISHED; tampered approve → `APPROVAL_REFUSED` in Firestore, no packet object.
- Local suites stay green with no credentials (`uv run pytest -q`, `pnpm e2e`); CI unchanged.
- Cost: `cost-status.sh` after the demo run — expected well under the $10 budget.

## Rollback / teardown

Per `docs/runbooks/demo-teardown.md`: disable schedules (none planned), drain queue, scale to zero, destroy only `teardown=required`-labeled resources after Tarik confirms. Terraform state makes it one reviewed `destroy`.

## Risks (one line)

The public API URL is a real exposed endpoint until teardown — bearer token + finite max instances + $10 budget cap the blast radius, and 5.6 removes it.
