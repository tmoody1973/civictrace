# CivicTrace handoff — 2026-08-21, ~02:30 CDT

For the next agent session. Read this, then `CLAUDE.md` ("How to Talk to Tarik"), then MOO-717. Supersedes `2026-08-20-slice5-services-live-moo710-next.md`. Plain English on purpose.

## 0. THE BAR (read this first — set on 2026-08-20, the hard way)

Tarik was rightly furious that MOO-710/711 were called "done" while the AI ran on fixture files. His words: **"a journalist should get the full experience"** and **"I have 11 days and you are cutting corners — build the damn full experience."** The standing rules that came out of it:

1. **No fixture AI anywhere in the demo path.** Fixtures are for local dev and CI only.
2. **"Done" = what a journalist would see is real.** Checklists don't close demo-path issues; **Tarik clicks through and accepts personally** before Done.
3. **Don't offer menus that scope down.** He picked "full product"; build it. Gate only cloud/billing/destructive actions and choices that are genuinely his (which real record becomes evidence).
4. Honest notes about what broke are valued and expected. He caught the fixture gap himself — never let that happen again.

## 1. Where we are (one paragraph)

**Slices 1–5 complete** (MOO-684…712, all verified) **plus the full-live upgrade**: all four agent roles (document evidence, delta investigator, quality reviewer, inquiry planner) run **live Gemini Flash** in the cloud (MOO-713 ✅, Tarik accepted personally); the vault **fetches canonical bytes live from the City's servers**, hash-verified (MOO-714 ✅); cloud replay is fully live end to end (28 ledger events, DELTA_STAGED + INQUIRY_STAGED + NOT_PUBLISHED + duplicate suppressed; ~$0.055 model spend, per-call `model_usage` lines in Cloud Logging). The **11-day full-product roadmap** is the Linear project "CivicTrace — Full journalist product (11 days)" (target 2026-08-31): MOO-715 ✅ (media corpus), MOO-716 ✅ (diarized transcript), **717 next** → 718 → 719 → 720 → 721 → 722 → 723. The dev environment stays LIVE; teardown (`infra/scripts/teardown-dev.sh`, dry-run default) only on Tarik's word after the demo video.

## 2. Pointers (do not re-derive)

| What | Where |
|---|---|
| Repo | `~/Projects/civictrace` · github.com/tmoody1973/civictrace · latest `8120eb1` · CI green (one flaky axe check on approval drawer — see gotchas) |
| Linear | Project "CivicTrace — Full journalist product (11 days)" — 715 ✅ 716 ✅ · **717 next** (media agent) → 718 (studio pane) → 719 (case intake) → 720 (multi-case) → 721 (watcher) → 722 (hosted+sign-in) → 723 (video/Devpost). Slice 5 project all Done incl. 713 (live AI) + 714 (live fetch). |
| Cloud | project `civictrace-dev-tm`, us-central1. API `https://civictrace-api-3dlvda27oq-uc.a.run.app` (bearer; `/health` not `/healthz`). Worker image `…/civictrace:moo714` + env `CIVICTRACE_RUNNER=adk`, `CIVICTRACE_LIVE_FETCH=1`, `CIVICTRACE_BQ_PREFILTER=1`. Firestore case `case-tid121-bronzeville-arts-tech-hub` currently 28 live-AI events. |
| Replay | `backend/scripts/publish_source_events.py --publish` (ORDERED: waits per event; repeatable). Reset first: delete Firestore case doc + `ledger_events` + `jobs` docs (+ packet objects if re-approving). Full replay ≈ $0.06 and ~4 min. |
| Studio | `cd frontend && pnpm dev` → localhost:3000; `.env.local` points at the CLOUD (bearer inside, gitignored). `cp .env.example .env.local` restores local. |
| Media fixture | Full ZND Committee 2026-07-28 recording: vault `gs://civictrace-dev-tm-civictrace-vault/znd-committee-2026-07-28.mp4` + local `backend/tests/fixtures/…/media/` (gitignored, 2.9GB; re-fetch recipe in `media/README.md`). Manifest: `media_artifacts` section, focus segment **5287→5990s** (= the TID 121 item, from Legistar's own `EventItemVideoIndex`, agenda item 493916). Segment FLAC also vaulted. |
| Transcript | `backend/tests/fixtures/…/transcripts/znd-2026-07-28-tid121.json` (COMMITTED, gitignore exception): 42 segments, 5 speakers (chair, Lori Lutzka DCD, FIT Investment Group developer, members). Schema `app/schemas/transcript.py`; service `app/services/transcription.py`; script `scripts/transcribe_segment.py`. |
| Learnings docs | `docs/research/gavel-learnings.md` (Gavel project = Tarik's June hackathon; Granicus recipe, Legistar client gotchas, speaker-naming gate, demo craft) · decision docs 001–004 · cost table in `docs/runbooks/demo-teardown.md` |
| Costs so far | Model ~$0.06 total (all live replays), STT $0.19, storage ~10.5MB + 2.9GB video. Budget $10 with alerts. `infra/scripts/cost-status.sh` sums cloud `model_usage` lines. |

## 3. MOO-717 — what the next session builds (Media Evidence agent)

1. **In Progress → 3–6 line plain plan in chat.** Then build; gate only cloud actions.
2. **MediaExtraction schema + validator** (mirror the document pattern in `app/schemas/evidence.py` / `app/services/validator.py`): every claim anchored to a transcript timestamp range within the focus segment; `speaker_label` stays a label (validator refuses treating it as a name); allegation/causal-language checks reused; discussion ≠ decision.
3. **Transcript-span tool** for the agent (mirror `ArtifactPageReader` in `app/tools/artifact_tools.py`): bounded reads of the committed transcript JSON — the agent sees spans, never the whole corpus.
4. **`media_evidence` role live**: prompt already versioned in `app/agents/prompts.py` (add the output-contract sentences like the others got — the validator WILL reject otherwise; that's how 713's first run failed). Route it in `agents_service.py` `live_roles`. Definition needs creating next to the others in `document_evidence.py` (output_model=MediaExtraction).
5. **Optional speaker naming** (Gavel's pattern, `docs/research/gavel-learnings.md` §3): roster + how-the-room-talks, 0.8 confidence gate, roster-officials-only; else keep the label. Committee roster via Legistar API bodies endpoint.
6. **Wire media evidence into the case bundle** as later evidence so the Delta Investigator can cite the hearing ("the developer described X at 1:33:20"). Follow the bundle-building path in `app/repositories/cases.py::build_case_bundle`.
7. **Prove it live** (local `--runner adk` first, then cloud), verification comment with a real quoted anchored evidence object + honest notes → **Tarik reviews in the studio before Done** (718 builds the pane; a JSON-level review is acceptable for 717 if he says so).

## 4. Hard-won gotchas (do NOT relearn these)

- **STT V2 diarization exists in exactly ONE pair: model `chirp_3` + location `us` (multiregion), endpoint `us-speech.googleapis.com`.** BatchRecognize refuses diarization at `global` and single regions; sync refuses on latest_long/long/telephony/chirp_2. Probed live 2026-08-20. chirp_3 emits NO per-word confidence → transcript confidences are null (UI keys on null, not thresholds).
- **Granicus 403s datacenter IPs** for archive MP4s (Gavel verified; we honored it). Media enters via operator machine → vault. Cloud only reads vault bytes.
- **Batch STT per-file errors are silent unless you raise on `file_result.error.message`** — a "successful" run once returned 0 segments because the Speech agent lacked vault read (now granted via Terraform).
- **Piping to `tail`/`grep` eats exit codes** — this bit us twice. Check `$?` of the real command.
- **Cloud Tasks has NO ordering** (ordered publish script exists) and **burns task names ~1h** (names now include Pub/Sub messageId). **BigQuery loads MUST pass explicit schema** or autodetect relaxes REQUIRED→NULLABLE and terraform REPLACES the table (data loss happened once). **Python drops INFO logs** unless basicConfig (worker opts in). **Playwright `reuseExistingServer` once sent e2e approvals to the REAL cloud** — config now pins local env; when e2e looks impossible, check who owns ports 3000/8000.
- Frontend e2e axe check `aria-valid-attr-value` (approval drawer) is FLAKY — failed a docs-only commit once; not a regression signal by itself.
- Legistar Web API is allowlisted and free for Milwaukee: events `EventMedia`=Granicus clip id, `EventItemVideoIndex`=item start second. **Amendment No. 1 was ADOPTED 2026-07-31 and SIGNED 2026-08-03 (matter 74415 histories)** — the source watcher (721) can answer the system's own staged inquiry ON CAMERA. Don't waste that demo beat.
- ego-browser can't inherit Tarik's Google login; **claude-in-chrome driving his real Chrome works** (used for all Console screenshots).

## 5. After 717

718 studio transcript pane (timestamp jump; null-confidence marking) → 719 case intake (Legistar file # → candidate bundle → human review; port recipes from Gavel's `mcp-server/`, gotchas in learnings doc §2) → 720 multi-case + live entity resolution → 721 source watcher (Cloud Scheduler + matters/histories queries; the adopted-amendment beat) → 722 hosted studio + real sign-in (bearer retires) → 723 demo video + Devpost (dry-run audit first, Gavel style; teardown only after submission proof, on Tarik's word).

## 6. Working with Tarik (unchanged, plus tonight)

Plain English, short sentences, one PM lesson per recap. In Progress → plain plan → build → REAL run → verification comment with pasted proof + honest notes → **his personal acceptance** → Done. Gates via AskUserQuestion only for real forks and cloud/destructive acts. When he's angry, the answer is working code fast plus one honest sentence of ownership — not apology paragraphs, not menus.
