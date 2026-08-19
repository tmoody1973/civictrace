# CivicTrace API contract (Slice 2) — what the Evidence Studio reads

Two read-only endpoints, no auth yet (`# ponytail: add user auth before any deploy`). Every response uses one
envelope. Every field comes from the case ledger (validated facts); there is no free-text summary field.

```json
{ "ok": true, "data": { ... }, "error": null }          // 200
{ "ok": false, "data": null, "error": "case 'x' not found" }   // 404
```

## `GET /healthz` → `{ "status": "ok" }`

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

Ordering guarantees: `ARTIFACT_STORED` precedes its `EVIDENCE_ACCEPTED` rows; `DELTA_PROPOSED` precedes
`DELTA_STAGED`/`CASE_HUMAN_REVIEW`; every id in a delta's `original_evidence_ids`/`later_evidence_ids`
appears earlier in the same trace as an `EVIDENCE_ACCEPTED` row.

Source of truth for field types: `backend/app/schemas/api.py`. Run it locally: `backend/README.md` → "Slice 1 — run it".
