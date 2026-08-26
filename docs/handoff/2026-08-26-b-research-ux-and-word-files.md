# CivicTrace handoff — 2026-08-26 (second of the day)

For the next agent session. Read this, then `CLAUDE.md` ("How to Talk to Tarik"), then the
issue you pick up. Supersedes `2026-08-26-moo720-accept-then-721.md`. **Five days to the
submission deadline (2026-08-31).**

## 0. THE BAR + today's two directives (Tarik's words, full weight)

The standing bar is unchanged: no fixture AI in the demo path; "Done" = Tarik clicks
through and accepts personally; every screen explains itself (`docs/product/ux-copy-guide.md`
is binding); narrate builds in plain English DURING the work, not just before and after.

Today he added two directives while reviewing as a first-time journalist:

1. **"This part is confusing for me — and if it is confusing for me, it would be for a
   journalist. Do research on this, not just from memory. I feel you are designing for a
   computer, not a human."** He did NOT say which screen — the next session's FIRST move
   on UX is to ask him to point at it (he was in the intake flow: search → role dropdowns
   → approve; and/or the entity-match trace rows). Then do real research — how
   DocumentCloud, MuckRock, CourtListener/RECAP, Big Local News, and Legistar InSite
   present records and name things — and suspect OUR invented framing ("the promise /
   later evidence", "candidate bundle") as the root confusion. This is now written into
   MOO-724's Approach. Redesign must cite research, not intuition.
2. **"We need to fix the Word file. There are a lot of Word files and we can't do
   anything — not good."** His real searches hit matters whose documents are Word files,
   where the product dead-ends. **MOO-726 is escalated to the demo path** (now High).
   Recommended build: convert .doc/.docx → PDF at intake (LibreOffice headless in the
   worker image), vault BOTH the canonical original (hash-locked) and the labeled
   conversion, run the existing page-anchor pipeline on the conversion; provenance cites
   the original; the no-silent-holes rule stands (excluded/converted files visibly noted
   on the case). Before building, re-sample Legistar attachments BY MATTER TYPE — the
   earlier "4% Word" figure was an average that hid the pain.

## 1. Where we are (one paragraph)

Repo head `fe629d2`, CI green, both cloud services on image `:moo749`. Everything through
MOO-719 is Done and accepted. **Awaiting Tarik's accept: MOO-720** (live entity matching,
cloud-proven, 14 links, zero cross-contamination) **and MOO-749** (plain-words search —
the intake front door is now "What are you looking into?"; deployed and live-verified:
"Amani homeownership" returns files 260500 and 260435 from the official record). He began
his acceptance run today and instead produced the two directives above — which IS the
process working. Two live cases exist (TID 121 Bronzeville; TID 136 Amani, created by him
through the product). The API keeps one warm instance through submission (documented
Terraform exception; ~$1–3; revert at teardown).

## 2. Pointers (do not re-derive)

| What | Where |
|---|---|
| Repo | `~/Projects/civictrace` · github.com/tmoody1973/civictrace · head `fe629d2` |
| Linear | Project "CivicTrace — Full journalist product (11 days)". Done 715–719. Awaiting accept: **720, 749**. Demo path remaining: **726 Word files (escalated) · 721 watcher · 724 UX (research-first) · 722 hosted · 723 video/Devpost**. Side: 725 clip embed. |
| Hackathon | All Things Agentic Hackathon (Devpost). Taskmaster + arch/multimodal awards. 40/30/30 judging. `docs/hackathon/official-requirements.md`. Due 2026-08-31. |
| Cloud | `civictrace-dev-tm`, us-central1, image `:moo749` on api+worker. API keeps 1 warm instance (exception documented in services/main.tf). CORS allows localhost **3000 and 3002** (`CIVICTRACE_CORS_ORIGINS` env — extend it if the studio moves ports again). |
| Local studio | **Port 3002** (`cd frontend && pnpm dev --port 3002`) — Tarik's other apps hold 3000 (Pennant Warden) and 3001 (Paper Majority). ALWAYS verify the page `<title>` says CivicTrace, never trust "the port answered": two apps can share a port across IPv4/IPv6. |
| e2e | Ports are env-overridable: `CIVICTRACE_E2E_WEB_PORT=3010 CIVICTRACE_E2E_API_PORT=8010 pnpm e2e`. The config passes the matching CORS origin to the e2e backend. Suite: 10/10 green at head. |
| Replays / deploy | Recipes unchanged — see the superseded 2026-08-26 handoff §2 (kept in repo) for the exact reset/publish/create-case and build/terraform commands. |
| 721 material | `docs/research/gavel-learnings.md` §2 (watcher window queries). The demo beat: Legistar shows Amendment No. 1 (matter 74415) ADOPTED 2026-07-31, SIGNED 2026-08-03 — the watcher discovers the answer to the system's own staged inquiry, on camera. Incremental-only is an official acceptance test. |

## 3. Next work, in order (5 days — this is tight; confirm order with Tarik)

1. **Ask Tarik which screen confused him** (one question, with a screenshot if he can),
   and collect his accepts or rejections on 720 and 749.
2. **MOO-726 Word files** — the pragmatic conversion path above. It is now the biggest
   real-use wall. (~1 day incl. image growth for LibreOffice; test with a real Word-heavy
   matter he found.)
3. **MOO-721 watcher** (~1 day) — the Taskmaster category's core proof + the on-camera
   discovery beat. Do not let steps 1–2 consume it; it is the hackathon's 40% column.
4. **MOO-724 UX** — research-first (see directive 1), then `/impeccable`, then reflow.
5. **MOO-722 hosted → MOO-723 video/Devpost** (dry-run audit first; teardown only after
   submission proof, on Tarik's word).

If time forces a cut, the cut is Tarik's call — present the tradeoff plainly (e.g. 725
clip embed and Excel support are already outside the line).

## 4. Hard-won gotchas (append-only; the 2026-08-26 morning list still applies)

- **Never truncate command output you might need** (`| tail` ate failure details twice
  today). Tee full logs to the scratchpad; read the whole verdict.
- **CORS is the "works in curl, fails in the browser" trap** — hit twice today (cloud API
  vs port 3002; e2e backend vs port 3010). If a pane says "Cannot reach the API" while
  curl succeeds, check the origin allowlist FIRST.
- **The e2e "API down" test blocks the env-derived port** now; keep any new fixtures/port
  references env-derived too.
- Background dev servers started with `nohup` from a tool shell die with the shell — use
  the session's supervised background runner, and expect Tarik to restart by hand with
  the one-liner above after the session ends.
- Next.js allows ONE dev server per project dir; a second `pnpm dev` on another port
  refuses with "already running" — kill the first (its PID is in the message).
- All older gotchas (429 self-heal, task-name burn, pypdf paraphrase retry, entity gate
  in code, media never re-fetched, chirp_3 quirks) are in the superseded handoff — still true.

## 5. Working with Tarik

Everything in the previous handoff §5, plus today's sharpened rule: **one plain sentence
before each meaningful build step** — what the product is getting, not which file is
edited. His persona reviews ("I am a first-time journalist") are the most valuable test
the project has; when one produces a critique, capture his exact words into the issue
before building anything.
