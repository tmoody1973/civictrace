# Fixture: milwaukee-city-promise-ledger-demo-v1 — TID 121 (Bronzeville Arts & Tech Hub)

Reviewed public-record replay corpus for CivicTrace Slice 1. Manifest: `docs/sources/corpus-manifest.yaml`.
Approved by Tarik Moody, 2026-08-19 (Linear MOO-685). Decision: `docs/decisions/002-first-case-is-a-tif-promise.md`.

## What is here

| Path | What it is | Provenance |
|---|---|---|
| `artifacts/tid121-project-plan-2024.pdf` | Project Plan, TID 121 — the Promise. Common Council file 240382, passed 2024-07-02. 31 pp. | Legistar matter 68373, attachment 223678. sha256 `7097a1ba…aefe1` |
| `artifacts/tid-annual-report-2024.pdf` | 2024 Annual TID Report (DCD communication). File 250623, placed on file 2025-07-31. 164 pp. TID 121 is on pp. 163–164. | Matter 71523, attachment 237082. sha256 `a2058b5f…124e6` |
| `artifacts/tid121-amendment-1-2026.pdf` | Amendment #1 to the TID 121 Project Plan. File 260433, passed 2026-07-14. 15 pp. | Matter 74415, attachment 248545. sha256 `0c5ce45b…706a41` |
| `provenance/matter-*.json` | The Legistar API record for each matter and its attachment list, as retrieved. | `https://webapi.legistar.com/v1/milwaukee/matters/{id}` |
| `provenance/annual-tid-report-matters-query-2026-08-19.json` | API query listing every "Annual Report of Tax Incremental Districts" communication. Newest is the 2024 report. This is the proof of absence for the 2025 report (`NOT_PUBLISHED`). | same API, `$filter=substringof(...)` |
| `fixture_extraction.json` | Hand-written, anchored `DocumentExtraction` per artifact. `FakeAgentRunner` returns this in Slice 1.5. Every `verbatim_excerpt` is verified to be a substring of the named page (`pdftotext -layout`, whitespace collapsed). | written by hand from the PDFs |

## Rules for this directory

- These PDFs are **unmodified public records**. Do not edit, crop, re-save, or OCR-in-place. If a file must change, add a new file and a new manifest entry with its own hash.
- No personal, student, or resident data. Page 163 of the annual report names a company's managing partner; the fixture extraction anchors institutional facts only and does not extract the name.
- The absence of the 2025 Annual TID Report is recorded as `NOT_PUBLISHED` as of 2026-08-19. It is not a finding that the report does not exist or that anyone acted improperly.
- Retrieval was read-only: public API + public attachment URLs. No login, no forms, no rate-limit bypass.

## Re-verify

```bash
cd backend/tests/fixtures/milwaukee-city-promise-ledger-demo-v1/artifacts && shasum -a 256 *.pdf
# expected:
# a2058b5f9d6c6cd25b0f9ad9b630f70e9aef027f3ae973e9eca874cdb55124e6  tid-annual-report-2024.pdf
# 0c5ce45b48c957c0cf3ab8eecdc2e7fd866a5c315c78598c1a4deb01b5706a41  tid121-amendment-1-2026.pdf
# 7097a1ba6af1fc2aaa60a1d3e9a2b366d63ab067a8e6b4e052b46e8400aaefe1  tid121-project-plan-2024.pdf
```
