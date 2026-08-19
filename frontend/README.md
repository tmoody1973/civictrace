# CivicTrace Evidence Studio Frontend

## Purpose

The frontend is an editor-facing **Evidence Studio**. Its core question is: **“Can I personally verify why the system says this changed?”** It must present original source material, source anchors, timeline, uncertainty, reviewer corrections, and approval controls. It is not a chat UI and must not expose model/provider keys or internal worker endpoints.

## Required Stack

| Layer | Choice |
|---|---|
| Application | Next.js, React, TypeScript |
| UI primitives | shadcn/ui and Radix UI |
| Complex components | Kibo UI registry |
| Evidence table | TanStack Table |
| PDF/record viewer | PDF.js/React PDF; preserve page anchors |
| Meeting media | Native accessible video/audio controls with timestamped transcript linking |
| Graph/timeline | Start simple; use an interactive graph only if it improves source inspection |

## First Screen: Decision Delta Studio

Build this desktop-first three-pane screen before any broad dashboard.

```text
Case and evidence rail | Original PDF/video/data source | Decision Delta and human review
                     └────────── Evidence timeline beneath all panes ──────────┘
```

The user must be able to select a case, read the original commitment, jump to the exact later source page/row/timestamp, see a clear `Verified`/`Unknown`/`Conflicting` state, correct a candidate entity/case link, and approve or reject an inquiry draft.

## Component Boundaries

- `components/layout/`: app shell, navigation, top bar, responsive/resizable pane layout.
- `components/evidence/`: source inspector, PDF highlight, media transcript, source anchor link, evidence timeline, provenance panel.
- `components/case/`: case rail, Promise Card, Decision Delta, uncertainty states.
- `components/meeting/`: meeting video/audio, transcript segments, brief preview.
- `features/`: typed query/mutation hooks and domain composition; no raw fetch calls embedded in visual components.
- `lib/api.ts`: authenticated typed backend API client. All model work happens on the backend.

## UI Acceptance Checks

1. Keyboard navigation reaches every pane, source anchor, and review control.
2. Every status has a text label and does not rely on color alone.
3. Video/audio is not autoplayed and has transcript text.
4. A user can open every Decision Delta source anchor in the original artifact.
5. Missing or conflicting evidence is visually explicit; do not hide it behind optimistic summary copy.
6. Approval is a deliberate final action that exposes the exact packet/artifact being approved.


## Evidence Trace: AI SDK Elements Integration

Use the AI SDK Elements `ChainOfThought` component as a collapsed **Evidence Trace** beneath the Decision Delta header. It must display deterministic ledger/validation milestones and precise source anchors; it must **not** expose raw model chain-of-thought, hidden prompts, or unverified model text. Read `docs/implementation/reasoning-visibility-ux.md` before implementing it.

The trace should show `Source preserved`, `Evidence extracted`, `Case candidate evaluated`, `Later evidence compared`, `Policy checks passed`, and `Human decision required`. The human approval step must stay visibly distinct from completed automated steps. The frontend receives this data from a typed `EvidenceTrace` API response based on ledger events, never directly from an LLM response.

## Slice 3 — run it (local)

```bash
# terminal 1: backend serving the replayed ledger (see backend/README.md "Slice 1 — run it")
cd backend && CIVICTRACE_LEDGER_JSON=/tmp/civictrace-ledger.json uv run uvicorn app.main:app --port 8000

# terminal 2: the studio
cd frontend && cp .env.example .env.local && pnpm install && pnpm dev
open http://localhost:3000/cases/case-tid121-bronzeville-arts-tech-hub

pnpm lint && pnpm typecheck && pnpm test      # ESLint, next typegen + tsc --noEmit, vitest
pnpm e2e                                      # Playwright: starts backend (fixture replay) + Next itself, walks the demo path
                                              # (card → trace → NOT_PUBLISHED → anchor → PDF p.3 → Matches ledger), keyboard-only
                                              # variant, axe (0 serious/critical), and the API-down words. No cloud needed.
```

Layout: case rail | original source (PDF pane, anchor jump, hash verdict) | Promise Card + Decision Delta; Evidence Trace
in the timeline pane. CI (`.github/workflows/ci.yml`) runs backend pytest/ruff/mypy and frontend lint/typecheck/unit/e2e on every push. Types in
`src/lib/api-types.ts` are a hand-written mirror of `backend/app/schemas/api.py`. API base URL:
`NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`). No AI/provider key exists in the browser.
Proof screenshots: `docs/hackathon/proof/moo-695-*.png`.
