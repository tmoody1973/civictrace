# CivicTrace API contract (Slices 2–3) — what the Evidence Studio reads

Four read-only endpoints, no auth yet (`# ponytail: add user auth before any deploy`). Every response uses one
envelope. Every field comes from the case ledger (validated facts); there is no free-text summary field.

```json
{ "ok": true, "data": { ... }, "error": null }          // 200
{ "ok": false, "data": null, "error": "case 'x' not found" }   // 404
```

## `GET /healthz` → `{ "status": "ok" }`

Any unmatched route or framework error uses the same envelope (`{ "ok": false, "data": null, "error": "Not Found" }`).
CORS: origins from `CIVICTRACE_CORS_ORIGINS` (comma-separated; default `http://localhost:3000`); `ETag` and
`X-CivicTrace-Content-Hash` are exposed to the browser.

## `GET /cases` → `CaseSummaryView[]` (the case rail; Slice 3, MOO-696)

Same shape as `GET /cases/{case_id}`, one per case, ordered by `case_id`. Empty ledger → `data: []`, still `ok: true`.

## `GET /artifacts/{artifact_id}/file` → the exact vaulted bytes (Slice 3, MOO-696)

`GET` or `HEAD`. Body is the stored artifact; headers: `Content-Type` = stored MIME type, `ETag: "<content_hash>"`,
`X-CivicTrace-Content-Hash: <content_hash>`, `Cache-Control: private, max-age=0`. The UI can hash the body and compare to
the `ARTIFACT_STORED` row's `content_hash` — "exact copy" is checkable. The file path comes from the ledger's own
`storage_uri`, never from the request; the server re-hashes on every read and answers 500 if the vault bytes drift.
Unknown id → 404 envelope `artifact 'x' not found`; a `NOT_PUBLISHED` artifact → 404 envelope `artifact 'x' is NOT_PUBLISHED`.

## `GET /cases/{case_id}` → `CaseSummaryView` (one-glance state)

| field | meaning |
|---|---|
| `case_id`, `case_topic` | from the corpus manifest |
| `state` | `NO_DELTA` · `DELTA_STAGED` (reviewer approved, awaiting human) · `HUMAN_REVIEW` (reviewer flagged) |
| `counts` | `artifacts_stored`, `evidence_accepted`, `not_published`, `extractions_rejected`, `deltas_proposed`, `deltas_rejected` |
| `latest_delta` | null, or: `category`, `neutral_summary`, `original_evidence_ids`, `later_evidence_ids`, `what_is_established[]`, `what_is_not_established[]`, `next_evidence_needed`, `limitations[]`, `requires_human_review`, `review_outcome`, `blocking_issues[]` |
| `next_evidence_needed` | copied from the latest delta for the header |

## `GET /cases/{case_id}/trace` → `TraceResponse` = `case_id` + ordered `events[]` of `TraceEventView`

Common fields on every row: `event_id`, `event_type`, `occurred_at`, `actor`, `artifact_id` (or case id for case rows), `canonical_url`, `status`, `reason`.

| `event_type` | extra fields the UI should render |
|---|---|
| `ARTIFACT_STORED` | `content_hash`, `canonical_url` — "we kept an exact copy; here is the fingerprint" |
| `ARTIFACT_NOT_PUBLISHED` | `reason`, `status=NOT_PUBLISHED` — the honest empty slot |
| `EVIDENCE_ACCEPTED` | `evidence_id`, `anchors[{anchor_type, anchor_value}]`, `verbatim_excerpt`, `neutral_statement`, `limitations[]`, `status` (`SUPPORTED` / `UNKNOWN` / …). **Render quote and statement side by side.** |
| `EXTRACTION_REJECTED` | `reason` — what the checks refused |
| `NO_MATERIAL_DELTA` | `reason`; may carry delta fields if the agent returned a structured "no change" |
| `DELTA_PROPOSED` / `DELTA_REJECTED` | `category`, `neutral_summary`, `original_evidence_ids`, `later_evidence_ids`, `what_is_established[]`, `what_is_not_established[]`, `next_evidence_needed`, `requires_human_review` (+ `reason` on rejected) |
| `DELTA_STAGED` / `CASE_HUMAN_REVIEW` | delta fields above + `review_outcome`, `blocking_issues[]`, `review_notes[]` |
| `INQUIRY_APPROVAL_ISSUED` | `approval_token_id`, `approval_reviewer`, `approval_expires_at` — a human authorized one action on one exact artifact hash (Slice 4) |
| `INQUIRY_APPROVAL_REJECTED` | `reason` — the human said no, with their note |
| `APPROVAL_REFUSED` | `reason` — validation failed closed (missing/mismatch/expired/revoked); every attempt gets its own row |

Ordering guarantees: `ARTIFACT_STORED` precedes its `EVIDENCE_ACCEPTED` rows; `DELTA_PROPOSED` precedes
`DELTA_STAGED`/`CASE_HUMAN_REVIEW`; every id in a delta's `original_evidence_ids`/`later_evidence_ids`
appears earlier in the same trace as an `EVIDENCE_ACCEPTED` row.

Source of truth for field types: `backend/app/schemas/api.py`. Run it locally: `backend/README.md` → "Slice 1 — run it".

## Slice 4 write endpoints (MOO-705, local only)

These exist only when the server runs live (`CIVICTRACE_LIVE=1 uv run uvicorn app.main:app --port 8000` — it replays the fixture corpus in-process at startup). A static-ledger server answers them 503 `approval needs the live server`. Reviewer identity is a typed name until Slice 5 auth. `# ponytail: local write endpoints; auth is the Slice 5 deploy gate.`

| endpoint | meaning |
|---|---|
| `GET /cases/{id}/inquiry` → `InquiryStagedView` | the staged proposal exactly as the reviewer must see it: `proposal` (question, scope, target, evidence ids, exclusions, limitations), `artifact_hash` (sha256 of the canonical proposal JSON — the bytes an approval binds to), `ttl_minutes`. 404 envelope if nothing is staged. |
| `POST /cases/{id}/inquiry/approve` body `{reviewer_name, artifact_hash}` → `ApprovalResultView` | the client MUST echo the hash it displayed. Match → token issued → packet rendered (4.3) → `{token_id, reviewer_name, expires_at, packet_hash, packet_path}`. Echo mismatch → **409** envelope `you approved different bytes than are staged`, `APPROVAL_REFUSED` row, nothing rendered. |
| `POST /cases/{id}/inquiry/reject` body `{reviewer_name, note}` → `null` | the human said no; `INQUIRY_APPROVAL_REJECTED` row carries the note. |
| `GET /cases/{id}/packet` → `PacketView` | `{markdown, packet_hash, packet_path}` of the last rendered DRAFT packet. 404 envelope `no packet has been rendered` before approval. |

New trace rows for the UI: `INQUIRY_STAGED` / `INQUIRY_REJECTED` (inquiry fields: `inquiry_type`, `proposed_question`, `scope_rationale`, `target_record_or_source`, `supporting_evidence_ids[]`, `excluded_requests[]`) and `PACKET_RENDERED` (`approval_token_id` etc.; `payload_ref` is the packet sha256).
