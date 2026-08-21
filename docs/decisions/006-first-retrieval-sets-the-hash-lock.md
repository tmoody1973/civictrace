# 006 — For journalist-started cases, the first official retrieval sets the hash-lock

**Date:** 2026-08-21 · **Issue:** MOO-719

## Decision

When a journalist starts a case from a Legistar file number, the system fetches each
selected document from the City's own servers at the moment of approval, computes its
fingerprint (a hash — a short code that changes if even one byte of the file changes),
and locks that fingerprint as the truth for the case. Every later read must match it.

## Why this came up

The demo case's documents were hash-checked against fingerprints a human recorded by hand
during review. A self-serve case has no such pre-recorded fingerprint — the journalist
reviews the official *listing* (titles, dates, links), not the raw bytes. We needed a rule
for when bytes become trusted, and getting it wrong would either block self-serve entirely
or let unverified bytes into evidence.

## Options

1. **Require a human to hand-verify every fingerprint first.** Maximum caution; kills the
   self-serve product — nobody will hash PDFs by hand.
2. **Trust whatever the URL serves, whenever it is fetched.** Simple, but then a silently
   changed document could enter evidence differently on different days.
3. **First retrieval locks the fingerprint.** The system fetches once at approval, from the
   allowlisted official domain only, records the fingerprint, and refuses any future bytes
   that differ. The human gate stays: a named reviewer must approve the bundle and assign
   roles before that fetch happens.

## What we chose and why

Option 3 (Claude proposed, consistent with the product rules; Tarik's standing direction
was the full self-serve experience). It buys self-serve speed while keeping the two
properties that matter: evidence only enters from official allowlisted servers, and once
in, it can never silently change — the pipeline itself re-fetches during processing and
the two fetches must agree.

## What we gave up

We cannot detect a document that was tampered with *before* our first fetch — the lock
starts at our first look, not at publication. We accept this: the fetch is from the
City's canonical server over HTTPS, the same trust anyone reading the public record has.

## How we'll know if this was right

A journalist creates a real second case end to end without touching a terminal, and the
refusal tests hold: off-allowlist URLs, non-document files, and unapproved bundles never
become cases. If the double-fetch check ever fires (bytes changed between approval and
processing minutes later), the design caught something real.

## What actually happened

_(Tarik fills this in.)_
