# 007 — Word files become PDFs at the door

## Decision

When a journalist picks a Word attachment, CivicTrace converts it to a PDF at intake and
keeps both files: the City's exact original (fingerprinted, untouchable) and the labeled
PDF copy the system actually reads.

## Why this came up

Tarik's first real searches as a journalist hit matters whose key documents are Word
files, and the product dead-ended: "we need to fix the word file. there are a lot of word
files and we can't do anything — not good." A fresh measurement (2026-08-26, ~240 matters
sampled across 2026's six biggest matter types) showed the earlier "4% of attachments"
average hid the real shape: Communications matters — 367 filed this year — have
attachments that are nearly half Word files, and Appeals hit Word files in a quarter of
sampled matters. Hearing notices and fiscal notes are the usual culprits. Five days from
the submission deadline, this was the biggest wall between a real journalist and a real
case.

## Options

1. **Teach the whole system to read Word natively.** Every trust check is built on "this
   quote is on page 5" — and a Word file has no fixed pages. We would need a new kind of
   anchor (paragraph numbers) through the extractor, the validator, and the viewer. The
   honest cost: several days of rework across the most safety-critical code, right before
   the deadline.
2. **Convert Word to PDF at intake, keep both files.** One new converter step (LibreOffice
   running headless — a mode with no screen, just file in, file out), no change to any
   trust check. Cost: the server image grows about 400 MB, and a conversion is a copy —
   so the case record must always say which file is the City's original and which is ours.
3. **Keep refusing Word files, label them clearly.** Zero build cost. But the measurement
   says this walls off much of the correspondence record — for a journalist tool, that is
   not a labeling problem, it is a product failure.

## What we chose and why

Option 2 (joint: Tarik escalated the problem and set the bar; Claude proposed the
conversion path in the 2026-08-26 handoff; Tarik picked it for the build). It reuses the
entire existing page-anchor trust chain unchanged and ships in a day. Provenance stays
honest: the original's fingerprint is what a re-download from the City must match,
forever; the conversion is marked as derived and is never re-fetched — the system just
confirms the vaulted copy is intact, the same rule meeting videos already follow.

## What we gave up

- Page numbers cited by the system are the **conversion's** pages, not pages the City ever
  published — a reader following a citation must use our PDF copy, not the original Word
  file. The case record says so.
- A ~400 MB heavier server image (slower cold starts, more storage).
- Excel files and scanned image-PDFs are still refused; the intake screen labels them.
- One converter (LibreOffice) becomes a load-bearing dependency; a Word file it cannot
  handle fails the case creation with a plain-English reason rather than degrading
  silently.

## How we'll know if this was right

A real Word-heavy Milwaukee matter (a Communication with a "Hearing Notice List" .docx)
goes from search to created case in the deployed product, with both files visible in the
vault and every quote anchor passing the existing checks. If journalists instead start
asking "why don't your page numbers match the City's file?", option 1's paragraph anchors
become worth their cost.

## What actually happened

_(Tarik fills this in later.)_
