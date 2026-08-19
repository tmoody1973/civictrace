# CivicTrace handoff — 2026-08-19, end of day

For the next agent session. Read this first, then `CLAUDE.md` (note the new last section **"How to Talk to Tarik"**), then the Linear issue you pick up. Everything below is plain English on purpose.

## 1. Where we are (one paragraph)

CivicTrace is an approval-gated public-evidence system. The hackathon MVP is a **City of Milwaukee Promise Ledger**: follow one public commitment through later public records, anchor every fact to a page, say what changed and what is still unknown, never accuse. Today we finished **Slice 1** (the evidence spine) and the **local half of Slice 2** (a Decision Delta + a second-look reviewer, both with stand-in AI). On a laptop, one command replays three real Legistar PDFs for **TID 121 (Bronzeville Arts & Tech Hub)** and ends with: *"DELTA_STAGED (REVISED) reviewer=APPROVE — 2024 plan $700,000 (p.5) → Amendment No. 1 $2,345,000 (p.3); next record: 2025 Annual TID Report."* 120 tests, ruff + mypy clean, all pushed.

## 2. Pointers (do not re-derive these)

| What | Where |
|---|---|
| Repo | `~/Projects/civictrace` · GitHub https://github.com/tmoody1973/civictrace (private, `main`, gh account `tmoody1973`) |
| Operating rules | `CLAUDE.md` (incl. "Agent skills", "Clean Code Standards", "How to Talk to Tarik"), `CONTEXT.md`, `.claude/rules/*.md` |
| Roadmap decision | `docs/decisions/003-full-mvp-in-six-slices.md` — **full PRD MVP, six slices, no half version** (Tarik confirmed twice) |
| Other decisions | `docs/decisions/001-where-work-is-tracked.md`, `002-first-case-is-a-tif-promise.md` · retro `docs/LEARNING-LOG.md` |
| Linear (team Moodyco, key MOO) | Slice 1 project (done): https://linear.app/moodyco/project/civictrace-slice-1-city-source-replay-945b71902277 · Slice 2 project: https://linear.app/moodyco/project/civictrace-slice-2-real-agent-decision-delta-local-4b766ccbf922 |
| Issue conventions | `docs/agents/issue-tracker.md`, `triage-labels.md`, `domain.md` (Linear for build work; every closed issue has a verification comment with real output) |
| API contract for the UI | `docs/implementation/api-contract.md` |
| How to run | `backend/README.md` → "Slice 1 — run it" (replay script + uvicorn + curl) |
| Fixture (real public records) | `backend/tests/fixtures/milwaukee-city-promise-ledger-demo-v1/` — 3 PDFs in `records/`, `fixture_extraction.json`, `fixture_delta.json`, `fixture_review.json`, `provenance/*.json`, `README.md` |
| Manifest + allowlist | `docs/sources/corpus-manifest.yaml`, `docs/sources/source-allowlist.yaml` (host `milwaukee.legistar1.com` added, documented) |
| Memory (auto-loaded) | `~/.claude/projects/-Users-tarikmoody-Projects-civictrace/memory/` — `civictrace-slice1-status.md`, `feedback-plain-english-always.md` |

## 3. Slice 2 board

| Issue | State | Plain meaning |
|---|---|---|
| MOO-690 GCP dev project + Vertex AI + local auth + $10 budget | **Open, Tarik-owned** | Needs Tarik's Google account and a card. **Claude's first job: write `docs/runbooks/local-vertex-setup.md`** (≤1 screen, 5 commands, verification commands, teardown). Plan-mode gate: new Cloud resource/billing. |
| MOO-691 Real Gemini Flash agent + grounding eval | Open, blocked by 690 | Replace the stand-in with a real ADK agent behind the **same seam** (`StructuredAgentRunner.run` in `backend/app/agents/factory.py`). Pull current ADK docs with `ctx7` first. Plan mode before coding. Eval compares model output to Tarik's hand-written fixtures. Fake stays default so CI needs no credentials. |
| MOO-692 Decision Delta | ✅ | promise pile vs later pile → delta → checks → `DELTA_PROPOSED` |
| MOO-693 Quality Reviewer | ✅ | second-look reviewer; only APPROVE + zero issues stages |
| MOO-694 Trace/API rows + case card | ✅ | `GET /cases/{id}` + `GET /cases/{id}/trace`; contract doc |

Slice 3 (Evidence Studio UI) is **not yet planned in Linear**. It can start now against `api-contract.md`; it does not need Google Cloud.

## 4. What the next session should do (in order)

1. **Write the MOO-690 runbook** (`docs/runbooks/local-vertex-setup.md`), add `.env.example` keys (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION=us-central1`, `CIVICTRACE_MODEL`), note budget threshold/recipient in `docs/runbooks/cost-security-and-claude-code.md`. Then hand it to Tarik; do **not** run gcloud for him. ~15 min.
2. **Plan Slice 3 in Linear** (`/linear-build` project kickoff, present issue list, STOP for yes): Next.js + shadcn/ui + Kibo UI, desktop-first Evidence Studio, AI SDK Elements ChainOfThought used only as the Evidence Trace of ledger rows; read `docs/implementation/reasoning-visibility-ux.md` and `frontend/README.md` **before** proposing (the "read the source materials" rule in `~/.claude/CLAUDE.md` — design files may exist; check `frontend/` and `docs/` first). Probably 4–6 issues: app shell + data client against the contract → case card → trace timeline (quote/statement side by side, page anchor, URL) → PDF page viewer with anchor jump → NOT_PUBLISHED + human-review states → Playwright smoke.
3. When Tarik reports MOO-690 done → **build MOO-691** (plan mode, `ctx7` for ADK, Flash only, usage log, live eval behind `CIVICTRACE_LIVE=1`).

## 5. How to work with Tarik (read `CLAUDE.md` "How to Talk to Tarik" — summary)

- Plain English, short sentences, define every term; **every explanation teaches one PM-level thing** (what it buys, what it trades away, the question a PM would ask). He said "I have no idea 95% of what this means" after a jargon plan — do not repeat that.
- He engages well with one **"what would you check first?"** question per load-bearing piece (the linear-build diff-question gate). Keep it to one.
- Flow that worked all day: move issue In Progress → 3–6 line plain plan (ask yes only when a rule requires: evidence schema, agent authority, new Cloud resource, user-visible conclusion) → tests first → code → real run → paste proof in a Linear verification comment → gate question → Done.
- Decisions where someone could reasonably have chosen differently go in `docs/decisions/NNN-*.md` in plain English with **"What actually happened" left blank** for Tarik.

## 6. Known gaps / honest notes (already recorded in issue comments)

- Source policy ignores port numbers; no minimum quote length; alias URL not recorded on a duplicate delivery; "true quote, false statement" is not deterministically catchable (reviewer + side-by-side UI mitigate).
- The real ADK runner (`GoogleAdkStructuredRunner`) is still pseudocode; `per-file-ignores` in `backend/pyproject.toml` cover its unused var and long prompt lines until 2.2.
- Slice 5 (Cloud deploy) is late in the roadmap by design; MOO-690 starts that clock early.

## 7. Suggested skills for the next session

`linear-build:linear-build` (issue = contract; kickoff for Slice 3), `superpowers:test-driven-development` / `tdd` (tests first, as all day), `context7-mcp` / `ctx7` CLI (live ADK + Next.js docs before coding MOO-691 and Slice 3), `frontend-design` + `vercel:shadcn` + `design-review` (Slice 3), `ego-browser` for UI checks, `socratic-builder` lightly (one question per piece), `documentation-and-adrs` (decision log entries). Plan mode (`EnterPlanMode`) before MOO-691 and before any Cloud resource.
