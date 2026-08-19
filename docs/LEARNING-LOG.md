# CivicTrace — Learning Log

Dated entries. Each answers: what did we expect, what happened, what do we now believe.
Claude drafts; Tarik edits in his own voice.

## 2026-08-19 — Slice 1 (City source replay, local, no model) built in one sitting

**What we expected.** The first slice — contracts, a real Milwaukee fixture, vault, idempotency, the
fake-agent boundary, a replay script and a trace API — would take a couple of days and the fixture hunt
would be the slow part.

**What happened.** Six Linear issues (MOO-684 → 689) went spec → tests → code → proof → Done in about
three hours, including picking and freezing a real TID 121 (Bronzeville Arts & Tech Hub) corpus from
the public Legistar API. 93 tests, ruff and mypy clean, one command replays the corpus, one URL serves
the Evidence Trace. Three small surprises, all caught by tests or checks rather than by luck:
`.gitignore` silently dropped the fixture PDFs because the folder was named `artifacts/`; a colon in a
YAML list item turned a string into a dict (the manifest schema caught it); two PDF text extractors
place table `$` signs differently, so the quote-on-page check compares words and digits ignoring
whitespace and `$`.

**What we now believe.**
- Freeze the fixture *before* writing the extraction code. Having real pages to anchor to made every
  later decision concrete (page 5 says $700,000; page 3 says $2,345,000; page 163 is blank).
- The "diff-question" gate at each issue earned its keep: "a number with no page", "a fake official URL",
  "same bytes new URL", "real words wrong meaning" each produced a pinned test or an honest "code can't
  catch that" note. The last one is the job of the Slice 2 Quality Reviewer and a side-by-side UI.
- The expected-but-absent 2025 Annual TID Report is the best demo moment: it forces the system to say
  `NOT_PUBLISHED` out loud instead of guessing.
- Keeping `schemas/` and `domain/` pure (stdlib + pydantic, enforced by a test) cost nothing and made
  every fake trivial to write.
