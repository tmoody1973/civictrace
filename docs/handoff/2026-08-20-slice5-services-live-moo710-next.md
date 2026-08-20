# CivicTrace handoff — 2026-08-20, evening

For the next agent session. Read this, then `CLAUDE.md` (note "How to Talk to Tarik"), then MOO-710. Plain English on purpose. Supersedes `2026-08-19-slices-1-2-3-done-slice4-planned.md`.

## 1. Where we are (one paragraph)

**Slices 1–4 are done** (MOO-684…706, all with verification comments; CI green). **Slice 5 (cloud deploy) is 3 of 6 issues in**: the Terraform baseline (MOO-707), the Firestore ledger + GCS vault code (MOO-708), and the deployed services (MOO-709) are Done. **CivicTrace is live in Google Cloud right now**: `civictrace-api` (public URL + bearer gate) and `civictrace-worker` (IAM-only) on Cloud Run, both min 0 / max 2, plus the Tasks queue, Pub/Sub topic, buckets, Firestore, secret. **Firestore is still EMPTY** — no cloud replay has run. That is MOO-710, the next issue: publish the 4 source events, watch the ledger appear, capture Console proof. Then MOO-711 (UI → cloud API) and MOO-712 (teardown + cost + decision doc 004).

## 2. Pointers (do not re-derive)

| What | Where |
|---|---|
| Repo | `~/Projects/civictrace` · https://github.com/tmoody1973/civictrace (public, `main`) · latest commit `181395c` · CI green |
| Slice 5 board | https://linear.app/moodyco/project/civictrace-slice-5-cloud-deploy-dev-969060a20a03 — 707 ✅ 708 ✅ 709 ✅ · **710 next** → 711 → 712 (blockers chained) · plan: `Plans/quiet-roaming-moler.md` |
| Cloud project | `civictrace-dev-tm`, region `us-central1`, billing acct `016196-8315AF-BC6FBE`, $10 budget `civictrace-dev-10usd`. ADC signed in locally. |
| **API (live)** | https://civictrace-api-3dlvda27oq-uc.a.run.app — `/health` open; everything else needs `Authorization: Bearer <token>`; token: `gcloud secrets versions access latest --secret civictrace-api-bearer --project civictrace-dev-tm` (keep it in a shell var, never print/commit; it was created by Tarik) |
| **Worker (live)** | https://civictrace-worker-3dlvda27oq-uc.a.run.app — IAM-only (403 unauth is correct). Deterministic alias `https://civictrace-worker-<projnum>.us-central1.run.app` also routes; the enqueuer env uses it. |
| Image | `us-central1-docker.pkg.dev/civictrace-dev-tm/civictrace/civictrace:moo709-r3` · build: `gcloud builds submit --project civictrace-dev-tm --region us-central1 --config infra/cloudbuild.yaml --substitutions _IMAGE=...:newtag .` (~1 min; `.gcloudignore` keeps upload small) |
| Terraform | `infra/terraform/environments/dev` (LOCAL state, gitignored — this machine only). Deploy vars: `-var deploy_services=true -var image=<full image uri>`. Modules: `baseline` (buckets/FS/SAs/secret/registry) + `services` (run/queue/topic). `deletion_protection=false` on services (dev is `teardown=required`). |
| Guardrails / cost | `infra/scripts/verify-guardrails.sh` (run before/after every deploy; currently 9 ok / 0 fail) · `infra/scripts/cost-status.sh` |
| Cloud code map | `app/services/cloud.py` (`CloudConfig.from_env`, `build_cloud_workflow`) · `app/worker.py` (push→task→workflow; poison msgs acked not retried) · `app/repositories/firestore_cases.py` (append-only, txn create-if-absent, `seq` order) + `firestore_jobs.py` · `app/services/gcs_artifact_vault.py` (`if_generation_match=0`) · `uri_bytes.py` (file://+gs:// resolver seam) · `packet_store.py` (Local/Gcs writers) · api cloud mode: `main.py::_cloud_app` (`CIVICTRACE_CLOUD=1`) |
| Local modes unchanged | `CIVICTRACE_LIVE=1` (in-process replay + write endpoints) · `CIVICTRACE_LEDGER_JSON` (static) · suite `uv run pytest` green with **no credentials** (Firestore tests need emulator: docker `gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators`, port 8686, `FIRESTORE_EMULATOR_HOST=localhost:8686`) |
| Memory (auto-loads) | `~/.claude/projects/-Users-tarikmoody-Projects-civictrace/memory/civictrace-slice1-status.md` |

## 3. MOO-710 — what the next session builds (in order)

1. **In Progress → 3–6 line plain plan in chat.** No plan-mode gate for the code; the two cloud actions below get explicit Tarik gates.
2. **BigQuery minimal, honestly used** (Tarik's call): Terraform dataset `civictrace_dev` + table `corpus_artifacts` in `modules/baseline` or a small module; `scripts/load_corpus_bigquery.py` loads manifest rows; the worker's prefilter step queries BQ for the artifact's manifest row instead of reading the manifest file directly (env-gated so local/fake mode is untouched). *Gate: terraform apply.*
3. **`scripts/publish_source_events.py`**: publishes the 4 corpus events + the duplicate to topic `civictrace-source-events`. *Gate: Tarik's go before publishing (writes to his project).*
4. **Verify the DoD in the cloud** (worker runs `CIVICTRACE_RUNNER=fake` by default — fixture agents, no model cost; `adk` optional later): Firestore chain matches local event types; vault holds 3 PDFs with hashes; `tid-annual-report-2025` NOT_PUBLISHED; duplicate suppressed; DELTA_STAGED + INQUIRY_STAGED present; tampered approve via cloud API → APPROVAL_REFUSED, no packet object.
5. **Console proof** to `docs/hackathon/proof/` (Cloud Run logs, Tasks queue, Pub/Sub, Firestore docs, GCS objects, BQ job) + `cost-status.sh` output. Verification comment → Done.

## 4. Honest notes / gotchas (learned the hard way today)

- **512Mi killed the api container at startup** (import footprint). Both services now 1Gi + startup CPU boost + explicit TCP probe. If a service hangs "Still creating" >5 min, read the revision's `system_event` log message.
- **Secret values from `openssl | gcloud secrets versions add` carry a trailing newline.** The api strips its configured token; if you add more secret-fed envs, strip them too.
- **Google's front end swallows the exact path `/healthz` on `run.app` domains** — the app never sees it. Cloud probes/checks use `/health`. Local tooling still uses `/healthz`.
- A failed Cloud Run create leaves the Terraform resource **tainted** → destroy/recreate blocked by `deletion_protection` unless the flag change applies first; `terraform untaint 'module.services[0].google_cloud_run_v2_service.api'` + apply updates in place.
- Firestore duplicate-test gotcha: rebuilding the workflow makes a fresh in-memory job repo — test ledger dedupe with `ledger.append(existing)`, and rerun on the SAME workflow (see `test_firestore_ledger.py`).
- The api service account deliberately has **no Vertex access**; only the worker can reach the model. Do not "fix" 403s by widening roles — run `verify-guardrails.sh` first.
- BQ worker wiring: keep the prefilter env-gated (e.g. `CIVICTRACE_BQ_PREFILTER=1` set only on the worker) so the local suite needs no BQ dep at runtime.
- Every `terraform apply`, event publish, or deploy: show the plan/payload, **wait for Tarik's explicit go**. He answers gate questions fast; AskUserQuestion for real forks.
- If he must run a command himself (secrets), give it as a `! `-prefixed line for the chat box and **verify it landed** (his first attempt silently didn't).

## 5. After 710

- **MOO-711**: local studio → cloud API. Bearer goes in `frontend/.env.local` (gitignored); attach `Authorization` header in `src/lib/api.ts` (both `getJson` and `postJson`). Screenshots + demo-script Console beat. e2e stays local/fake.
- **MOO-712**: `infra/scripts/teardown-dev.sh` (dry-run default, fails closed on label/project mismatch), cost proof, `docs/decisions/004-slice5-cloud-shape.md` (three calls: local UI / BQ minimal-in / public+bearer; "What actually happened" left blank for Tarik). **Never destroy anything without his explicit word** — demo video may not be recorded yet.
- After Slice 5: Slice 6 (meeting media, STT V2) still unplanned — plan it in Linear first.

## 6. How to work with Tarik (proven again today)

Plain English, short sentences, define terms; each recap teaches one PM-level thing. In Progress → plain plan → tests first → code → **real run** → verification comment with pasted proof + honest notes → Done. He says "continue"/"next"; gates via AskUserQuestion. Honest-note sections (what broke, what I missed) have landed well every time — keep them.
