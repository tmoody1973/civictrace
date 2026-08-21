# What CivicTrace takes from Gavel (reviewed 2026-08-20)

Gavel (`~/Documents/Projects/gavel-slack-agent`) is Tarik's shipped June 2026 Slack-hackathon
agent: proactive Milwaukee civic alerts, 927 tests, deployed on Fly. It already paid for
lessons CivicTrace's Slices 6–9 need. Verified claims below cite Gavel's own code comments.

## 1. Meeting video — the whole recipe exists (feeds MOO-715/716/717)

- **Where the video lives:** Legistar's `EventMedia` field on an event IS the Granicus clip id.
  Player: `https://milwaukee.granicus.com/MediaPlayer.php?clip_id=<EventMedia>`. The player
  page names a direct, HTTP-range-seekable MP4 at `archive-video.granicus.com/...mp4`
  (`agent/transcripts/video.js: extractArchiveMp4`). The clip ids I found for TID 121
  (5262 ZND 7/28, 5265 Council 7/31) are these Granicus ids.
- **Per-agenda-item timestamps come FREE:** `EventItemVideoIndex` on an agenda item is the
  second that item starts in the video. No blind search of a 3-hour recording — jump straight
  to the TID 121 item.
- **THE LANDMINE (Gavel verified 2026-07-12, don't relearn it):** Granicus serves the player
  page to anyone but **403s the archive MP4 from datacenter IPs** — every header combo fails
  from Fly; identical request works from a residential IP. **Cloud Run will hit the same
  wall.** CivicTrace's answer: fetch media at ingest from Tarik's machine into the GCS vault
  (vault-first design already wants this); the cloud worker reads vault bytes, never Granicus.
- **Clipping:** ffmpeg range-fetch on the direct MP4 with a browser User-Agent — a 90s clip
  from a 3-hour webcast in seconds. Avoid the HLS endpoint (throttled ~0.45× realtime).
  Avoid yt-dlp as downloader (its Granicus extractor fails intermittently); use it for
  nothing — scrape the player page for the MP4 URL instead.

## 2. Legistar client recipes — port from `mcp-server/` (feeds MOO-719/721)

Gavel's own open-source **milwaukee-civic-mcp** wraps Legistar as 9 tools with a structured
error contract (`information_unavailable` instead of throwing). Port the recipes to the
Python intake/watcher; the gotchas are the value:

- **Voice votes return EMPTY votes** — most routine Milwaukee items have no roll call. Use
  `EventItemPassedFlagName` as the coarse pass/fail signal.
- **Matter titles are terse** (`"File 230045"`). Substance fallback chain: title → full
  matter text (`/matters/{id}/versions` → `/texts/{id}`) → first attachment.
- **Hard 1,000-row cap** on every list endpoint; page with `$top`/`$skip`.
- **Milwaukee needs no API key**; other cities may. `client` slug parameterizes everything
  (~300 municipalities run Legistar — the expansion story).
- Watcher window queries (`poller/legistar.js`): future window filtered
  `EventAgendaStatusName eq 'Final'` for upcoming agendas; separate 30-day LOOK-BACK window
  for video (footage exists only after a meeting).
- Devpost angle: CivicTrace's intake standing on the open-source MCP server Tarik shipped in
  June is a cross-project story judges can verify.

## 3. Speaker naming with a confidence gate (feeds MOO-717)

`transcripts/speakers.js`: diarization gives "Speaker 2"; a journalist can't publish that.
Gavel maps labels to officials from how the room talks (who chairs, who is thanked, who is
addressed by name) against the committee roster — behind a **0.8 confidence threshold and a
roster-officials-only rule: a wrong name is worse than no name.** This is CivicTrace's
"diarization label ≠ identity" rule made useful instead of merely safe. Adopt the pattern;
keep our validator as the hard back-stop.

## 4. Transcription boundary design (feeds MOO-716)

Gavel: Deepgram Nova-3, diarize+utterances+timestamps, `fetchFn` injected so mapping is
unit-tested with no network — same seam shape CivicTrace plans. We stay on **Speech-to-Text
V2** (Google-stack hackathon), but if V2 diarization disappoints on chamber audio, Gavel is
the evidence that this audio IS transcribable well — the problem would be the tool, not the tape.

## 5. Demo & submission craft (feeds MOO-723)

- **`docs/JUDGE-TESTING.md`** — a "7 minutes, nothing to install" self-serve script for
  judges, with a starred Test 1 that shows the core idea first. CivicTrace must ship one
  once hosted access (Slice 9) exists.
- **`docs/DEMO-DRY-RUN.md`** — a beat-by-beat readiness audit against the live deploy BEFORE
  recording. It caught that the script's hero item wasn't the seeded hero item. Run the same
  audit before the CivicTrace video.
- **README leads with a true story with stakes** (the Hope Ave "computational research
  facility" data center; residents won but at enormous cost). CivicTrace's equivalent lead:
  the TID 121 promise that grew from $700,000 to $2,345,000 in public records nobody reads —
  and the missing 2025 report the system watches for. Write the README/Devpost that way.
- **Positioning sentence discipline:** "It is not a chatbot. Nobody asks it anything." →
  CivicTrace's: "It is not a chatbot. It is an evidence ledger with a human gate."

## 6. Candidate ideas (not committed)

- **Bilingual output** (Gavel writes Spanish natively via a civic glossary in the prompt, no
  translation API; both languages on one card). Strong equity story for inquiry packets and
  briefs. Post-Slice-9 candidate — decision doc if adopted.
- Gavel's journal/ dev-diary and 927-test discipline: the practices are already CivicTrace's;
  keep them.

## What we deliberately do NOT copy

Slack-specific surfaces (Block Kit, RTS, Socket Mode), Convex vector memory (CivicTrace's
bounded-evidence design intentionally has no vector store in the MVP), and Fly hosting.
Gavel indexes and alerts; CivicTrace preserves, validates, and gates. Different jobs.
