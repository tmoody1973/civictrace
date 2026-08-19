# CivicTrace handoff — 2026-08-19, evening

For the next agent session. Read this, then `CLAUDE.md` (note "How to Talk to Tarik"), then the Linear issue you pick up. Plain English on purpose. Supersedes `2026-08-19-slice2-local-done.md`.

## 1. Where we are (one paragraph)

**Slices 1, 2, and 3 of six are complete** (decision 003: full MVP, six vertical slices, never a thinner product). The evidence spine, a **real Gemini Flash Document Evidence agent** (behind the same seam; fake stays default), and the **Evidence Studio UI** (case card, Decision Delta, Evidence Trace, PDF anchor-jump with hash proof, Playwright + axe + green CI) all work locally against the real TID 121 (Bronzeville) corpus. The repo is **public with an MIT license** and a full-product README. **Slice 4 is planned in Linear** (approval token + inquiry packet + failed-approval demo, MOO-702…706) — nothing in it is built yet. Backend 135 tests, frontend 29 unit + 3 e2e, ruff/mypy/eslint/tsc clean, CI green on every push.

## 2. Pointers (do not re-derive)

| What | Where |
|---|---|
| Repo | `~/Projects/civictrace` · https://github.com/tmoody1973/civictrace (**public**, MIT, `main`, gh `tmoody1973`) · CI `.github/workflows/ci.yml` (frontend job runs in `mcr.microsoft.com/playwright:v1.62.1-noble`; stock runner hangs on browser install) |
| Rules | `CLAUDE.md`, `CONTEXT.md`, `.claude/rules/*.md` · decisions `docs/decisions/001–003` |
| Linear (team Moodyco) | Slice 1 ✅ · Slice 2 ✅ · Slice 3 ✅ · **Slice 4 open**: https://linear.app/moodyco/project/civictrace-slice-4-human-approval-inquiry-packet-local-9bfd95030ec3 · backlog: MOO-701 (trace coverage line, needs-triage) |
| Cloud (MOO-690 done) | project `civictrace-dev-tm`, billing acct 1, $10 budget `civictrace-dev-10usd`, ADC signed in. **Model: `gemini-3.7-flash` at `GOOGLE_CLOUD_LOCATION=global`** — Gemini 3.x Flash exists ONLY in `global`; us-central1 has the 2.5 family. Runbook: `docs/runbooks/local-vertex-setup.md` (incl. list-models one-liner). |
| Run everything | backend: `backend/README.md` ("Slice 1 — run it" + "Slice 2.2 — --runner adk") · frontend: `frontend/README.md` ("Slice 3 — run it"; `pnpm e2e` boots both servers itself) |
| API contract | `docs/implementation/api-contract.md` (4 read endpoints incl. `GET /cases`, `GET /artifacts/{id}/file` with hash headers) |
| Real-agent bits | seam `StructuredAgentRunner` · real runner `backend/app/agents/factory.py::GoogleAdkStructuredRunner` (google-adk 2.7.1; injectable `run_agent` for offline tests) · one tool `app/tools/artifact_tools.py` (≤10 pages, own artifact only) · routing `app/agents/routing_runner.py` (only `document_evidence` → ADK) · cost `usage.jsonl` (~$0.016/replay) · eval `CIVICTRACE_LIVE=1 uv run pytest tests/evaluations -q` → report in `docs/evaluations/runs/` (5/5 pass) |
| UI bits | `frontend/src/features/{case,trace,artifact}` · window-event bridges: `evidence-focus.ts` (chips→trace) and `artifact-jump.ts` (anchors→PDF) · copy maps tested against backend `ALLEGATION_TERMS` |
| Proof screenshots | `docs/hackathon/proof/` (moo-695…700 PNGs) |
| Memory (auto-loads) | `~/.claude/projects/-Users-tarikmoody-Projects-civictrace/memory/civictrace-slice1-status.md` (running log of the whole day) |

## 3. Slice 4 board (all Backlog, blockers set 702→703→704→705→706)

| Issue | Plain meaning |
|---|---|
| MOO-702 | ApprovalToken (case + **exact artifact hash** + action + reviewer + expiry) + deterministic service; every refusal reason is a ledger event. Start here; pure code. |
| MOO-703 | Inquiry Planner behind the same seam, fixture first (`fixture_inquiry.json`: "has the 2025 Annual TID Report been published?"); `validate_inquiry` refuses accusation words / foreign evidence ids; `INQUIRY_STAGED`. |
| MOO-704 | Deterministic packet renderer, DRAFT-only, token-gated. **Token binds to the sha256 of the proposal the human saw** — edit after approval invalidates. Refusal writes `APPROVAL_REFUSED`, no file. |
| MOO-705 | Approval drawer in the studio + first write endpoints (`approve` echoes the hash; mismatch → 409 "you approved different bytes than are staged"). Reviewer identity = typed name until Slice 5 auth (say so in the UI). |
| MOO-706 | Playwright approve / reject / failed-approval + axe; update the demo script beat 2:10–2:35. |

## 4. What the next session should do (in order)

1. **Build MOO-702** (In Progress → 3–6 line plain plan → tests first → code → real run → verification comment → Done). No plan-mode gate needed: no new model path, no cloud resource. ~45 min.
2. 703 → 704 → 705 → 706 the same way. 704's hash-binding and 705's hash-echo are the load-bearing pieces; keep the diff-question for those two.
3. After Slice 4: **plan Slice 5 in Linear** (cloud deploy: Cloud Run api+worker, Firestore, GCS vault, Pub/Sub, Tasks, IaC in `infra/terraform`, guardrail script, teardown). Plan-mode gate applies (new cloud resources + billing). Read `.claude/rules/gcp-operations.md` + `infra/README.md` first. MOO-690's dev project is the start; everything else is new.

## 5. How to work with Tarik (unchanged, proven all day)

Plain English, short sentences, define terms; each explanation teaches one PM-level thing (what it buys, what it trades, the question a PM asks). One "what would you check first?" question per load-bearing piece — he answers them well (today: chose hash-verification first; ranked omission as the top model risk). Flow: In Progress → plain plan → yes only when a rule requires → tests first → real run → proof in Linear comment → gate question → Done. He says "continue"/"next" to keep going; AskUserQuestion for real forks (he picked billing account and model via it today).

## 6. Honest notes / gotchas

- With `--runner adk` the case ends **NO_DELTA on purpose**: the fixture delta cites hand-written evidence ids, live evidence ids differ, bundle check refuses (`DELTA_REJECTED … not in bundle`). Fail-closed until the real Delta agent (was 2.3/2.4 — fold into a later slice or an issue when needed; grounding eval was the 691 deliverable, not delta-on-live).
- Live eval history: first run missed plan p.5 + blank-status UNKNOWN; fixed via the bounded task message (not the versioned prompt). Both runs recorded in `docs/evaluations/README.md`.
- Red-team ranking from Tarik's gate (MOO-691 comment): omission > true-quote/false-frame > PDF injection > implication-without-allegation-words > UNKNOWN flooding > cost. MOO-701 is the omission counter-feature.
- ego-browser: `openOrReuseTab(url,{wait:true})` + `captureScreenshot()` (returns a path); `gotoUrl/gotoAndWait` hung; kill stale `ego-browser nodejs` procs; `js()` needs `JSON.stringify`-built selectors; axe = eval `node_modules/axe-core/axe.min.js` via `js()`. Close spaces with `completeTaskSpace(name,{keep:false})`.
- Start dev servers detached (`nohup … &`) — they died twice when their parent shell timed out. `pnpm e2e` is the reliable way to run both.
- pdf.js detaches ArrayBuffers → the viewer feeds it a blob URL (never revoked, 3 docs, noted `# ponytail:`).
- Known small gaps still open from Slice 1 notes: source policy ignores ports; no minimum quote length; alias URL not recorded on duplicate delivery.

## 7. Suggested skills

`linear-build:linear-build` (issue = contract), `tdd`, `ctx7` CLI before any new library (worked for ADK/shadcn/Kibo/AI-Elements/react-pdf), `ego-browser` for UI proof, plan mode (`EnterPlanMode`) before Slice 5 cloud work, `documentation-and-adrs` for any decision worth logging (`docs/decisions/NNN`, leave "What actually happened" blank for Tarik).
