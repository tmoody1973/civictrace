# MOO-710 — first cloud replay, CLI proof (2026-08-20)

All output below was captured live from project `civictrace-dev-tm` on 2026-08-20 (UTC times).
Runner: `CIVICTRACE_RUNNER=fake` (reviewed fixture agents) — **zero model spend**.

## 1. Ordered publish (4 events + 1 duplicate)

```
published .../tid121-project-plan-2024  → message 21496292812708120   job sha256:e4eedeedeb3a1507d… → SUCCEEDED
published .../tid-annual-report-2024    → message 21494054265952298   job sha256:49bcc4c655bb02e3b… → SUCCEEDED
published .../tid121-amendment-1-2026   → message 21494274392234674   job sha256:f3060dc041bc31f96… → SUCCEEDED
published .../tid-annual-report-2025    → message 21496292050265675   job sha256:92a022b58cd3e20f9… → SUCCEEDED
published .../tid121-project-plan-2024  → message 21495432912119241   job already terminal; duplicate suppression expected
```

## 2. Firestore ledger equals the local replay exactly

```
local 17 events / cloud 17 events
event ids EQUAL and IN ORDER: True
event types EQUAL: True
```

Chain (seq order): ARTIFACT_STORED, EVIDENCE_ACCEPTED ×3, NO_MATERIAL_DELTA,
ARTIFACT_STORED, EVIDENCE_ACCEPTED ×3, NO_MATERIAL_DELTA, ARTIFACT_STORED,
EVIDENCE_ACCEPTED ×2, DELTA_PROPOSED, **DELTA_STAGED**, **INQUIRY_STAGED**,
**ARTIFACT_NOT_PUBLISHED** (tid-annual-report-2025, with the reviewed absence basis).

Duplicate suppressed, one chain only: 5 ingest task requests in the worker log,
17 events, 4 job documents. The 5th run hit the persisted job ledger and wrote nothing.

## 3. GCS vault: 3 PDFs, immutable, provenance metadata

```
gs://civictrace-dev-tm-civictrace-vault/tid-annual-report-2024.pdf
gs://civictrace-dev-tm-civictrace-vault/tid121-amendment-1-2026.pdf
gs://civictrace-dev-tm-civictrace-vault/tid121-project-plan-2024.pdf
```

`tid121-project-plan-2024.pdf` custom metadata (excerpt):
`content_hash=sha256:7097a1ba6af1fc2aaa60a1d3e9a2b366d63ab067a8e6b4e052b46e8400aaefe1`,
`canonical_url=https://milwaukee.legistar1.com/...`, `source_id=milwaukee_legistar`.

## 4. BigQuery prefilter — honestly used, one query job per event

`INFORMATION_SCHEMA.JOBS`, worker service account (`civictrace-worker@…`):

```
21:36:12 QUERY 812B   21:36:17 QUERY 812B   21:36:22 QUERY 812B
21:36:28 QUERY 812B   21:36:33 QUERY (duplicate's prefilter)
```

Timestamps match the 5 `POST /tasks/ingest-source-event` requests one for one.
An event with no `corpus_artifacts` row is refused before any agent runs
(proven live at 21:30:12: `artifact ... has no corpus_artifacts row; event refused`).

## 5. Tampered approval refused by the live API, fail closed

```
POST /cases/case-tid121-bronzeville-arts-tech-hub/inquiry/approve   (wrong artifact_hash)
→ 409 {"ok":false,"data":null,"error":"you approved different bytes than are staged"}
```

Ledger seq=18: `APPROVAL_REFUSED` (durable, auditable).
Packets bucket: **empty** — no packet object was created.

## Console screenshots (captured 2026-08-20 via Claude driving Chrome)

ego-browser could not inherit the Google Console session (2 sign-in attempts), so the
PNGs are still to capture. One click each, save as `moo-710-*.png` in this folder:

1. Firestore case: https://console.cloud.google.com/firestore/databases/-default-/data/panel/cases/case-tid121-bronzeville-arts-tech-hub?project=civictrace-dev-tm
2. GCS vault objects: https://console.cloud.google.com/storage/browser/civictrace-dev-tm-civictrace-vault?project=civictrace-dev-tm
3. Tasks queue: https://console.cloud.google.com/cloudtasks/queue/us-central1/civictrace-ingest/tasks?project=civictrace-dev-tm
4. Pub/Sub topic metrics: https://console.cloud.google.com/cloudpubsub/topic/detail/civictrace-source-events?project=civictrace-dev-tm
5. Worker logs (21:36Z window): https://console.cloud.google.com/run/detail/us-central1/civictrace-worker/logs?project=civictrace-dev-tm
6. BigQuery job history (worker SA queries): https://console.cloud.google.com/bigquery?project=civictrace-dev-tm&ws=!1m0 → Job history → Project history

## 6. Cost

`cost-status.sh` at 21:39Z: budget `civictrace-dev-10usd` in place; both Cloud Run
services max 2 / min 0; vault 10.5 MB; packets 0 B; no `usage.jsonl` rows because the
replay ran on fixture agents (no Vertex calls, model cost $0).
