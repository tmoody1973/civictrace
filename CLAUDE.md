# CivicTrace — Claude Code Operating Contract

## 1. Mission and Current Scope

CivicTrace is an approval-gated public-evidence system for local accountability. It turns an official public commitment into a living, source-linked case file, detects when later public records materially change the evidence, and prepares a human-reviewable inquiry or meeting brief.

**Hackathon MVP:** A reproducible **City of Milwaukee Promise Ledger** replay loop. The system ingests one reviewed public Legistar/City dataset source bundle, preserves raw artifacts, extracts anchored evidence, links it to one case, produces a grounded Decision Delta or explicit uncertainty, and renders a human-approved inquiry packet.

**Not in the MVP critical path:** Citywide general monitoring, autonomous outreach/publishing, public-records filing, County expansion, dynamic procurement scraping, TinyFish/Parallel integration, MPS live monitoring, email/CMS integration, or a generic chat assistant.

## 2. Non-Negotiable Product Rules

1. **Evidence before prose.** Every material claim has an original public artifact ID and a precise page, table, JSON-row, transcript, video/audio timestamp, or map-feature anchor.
2. **Unknown stays unknown.** Use `UNKNOWN`, `NOT_PUBLISHED`, `CONFLICTING`, `CANDIDATE_LINK`, `REQUEST_NEEDED`, or `HUMAN_REVIEW` when the record does not support a conclusion.
3. **Models propose; code validates.** An LLM cannot directly mutate a case, grant approval, trigger an external side effect, or write a user-visible factual conclusion without deterministic validation.
4. **No unsupported allegations.** Do not infer or assert wrongdoing, fraud, corruption, illegality, motive, negligence, causation, or project failure from public-record gaps, delay, or conflict.
5. **MPS privacy boundary.** Never ingest, index, infer, log, display, or export individual student attendance, grades, discipline, disability, health, address, family, or personal data. MPS scope is public institutional information and public aggregate outcomes only.
6. **No autonomous external action.** The system never publishes, emails, contacts an official, or files a records request. A human must approve the exact case-bound artifact; approval expires and is audited.
7. **Direct official sources are authoritative.** A third-party research/extraction provider may produce only a candidate URL. CivicTrace must independently retrieve and preserve the canonical public source artifact before it becomes evidence.
8. **No hidden source expansion.** New sources require an explicit source-policy change, terms/rate review, fixture, and test.
9. **Cost and security by design.** Gemini Flash is the default. Cloud Run uses minimum instances `0` and finite maximums. Secrets live in Secret Manager. Browser clients never receive AI/provider keys.

## 3. Required Technology Choices

| Concern | Required choice |
|---|---|
| Agent backend | Python + Google ADK |
| Production inference | Gemini through Vertex AI, defaulting to Gemini Flash |
| Runtime | Cloud Run API service plus IAM-authenticated internal worker |
| Durable state | Firestore for cases, jobs, approvals, corrections, and ledger events |
| Raw artifacts | Cloud Storage, immutable metadata/hash/provenance first |
| Asynchronous work | Pub/Sub event fan-out and Cloud Tasks with idempotency/retry caps |
| High-volume structured corpus | BigQuery filtering before any model context is constructed |
| Meeting media, after City loop passes | Cloud Speech-to-Text V2 batch transcription plus Media Evidence Agent |
| UI | Next.js/React/TypeScript with shadcn/ui + Kibo UI; desktop-first Evidence Studio with AI SDK Elements Evidence Trace |

Do not add Antigravity SDK, Genkit, a second UI framework, a dedicated vector database, an always-on cluster, TinyFish, or Parallel to the MVP without a documented architectural decision.

## 4. Read Before You Change

| Task | Required documents |
|---|---|
| Product scope, domain model, user flow | `docs/product/PRD.md` and `CONTEXT.md` |
| Evidence Studio or AI SDK Elements | `docs/implementation/reasoning-visibility-ux.md` and `frontend/README.md` |
| Agent prompts, schemas, agent/tool boundaries, orchestration states | `docs/architecture/multi-agent-design-and-prompts.md` |
| ADK, Cloud Run, Vertex, Firestore, queues, or service design | `docs/architecture/google-agent-stack-decision.md` |
| Source adapter, external API, TinyFish, Parallel | `docs/integrations/api-stack-and-vendor-decision.md` and `docs/sources/source-allowlist.yaml` |
| Milwaukee source work | `docs/research/milwaukee-go-no-go.md` |
| MPS/meeting monitor work | `docs/research/mps-meeting-monitor-and-expansion.md` and `.claude/rules/privacy-and-evidence.md` |
| Hackathon/demo/submission | `docs/hackathon/` |
| Cloud/deployment/teardown | `.claude/rules/gcp-operations.md`, `infra/README.md`, and `docs/runbooks/` |

Read the smallest relevant set. Do not paste all project documents into an agent prompt.

## 5. Claude Code Workflow

### Plan mode is mandatory before:

- Any new Cloud resource, IAM role, source domain, external API, data category, model change, deployment, retention-policy change, or teardown.
- Any change to agent authority, evidence schema, approval token, privacy boundary, or user-visible civic conclusion.
- Any MPS feature or new type of meeting/media input.

In plan mode, state: objective; files to change; source/data/access impact; cost impact; test fixtures; acceptance criteria; rollback/teardown impact. Wait for human confirmation before deploy, billing, source enrollment, external integration, or destructive action.

### Implementation rules

- Make the smallest coherent vertical slice; avoid broad empty scaffolding.
- Start from schemas and tests, then deterministic services, then agents, then API/UI.
- Use dependency injection for storage, queues, model invocation, and time so tests can use fakes.
- Keep Pydantic/domain contracts independent of FastAPI, ADK, and Google Cloud SDK imports.
- Give ADK agents read-only, bounded tools. Agents return typed proposals only.
- Compute idempotency from source version/artifact hash/job type/agent version/case scope. Persist it before processing side effects.
- Store raw artifacts before extraction; preserve URL, source ID, retrieval time, MIME type, hash, and parser/model version.
- Render user-facing prose from validated fields rather than presenting unvalidated model text.
- Use `draft_only` as the default for all inquiry/brief artifacts.

### Required test behavior

Before merging code that touches ingestion, model prompts, source policy, entity/case links, approvals, or UI evidence display, run the relevant unit/integration/evaluation suites. At minimum preserve:

1. 100% material Decision Delta anchor coverage: original + later source evidence.
2. Duplicate-event suppression.
3. Missing-source explicit state.
4. Conflict preservation.
5. Candidate-versus-confirmed entity distinction.
6. MPS privacy denial.
7. Approval-gate failure closed.

## 6. Multi-Agent Control Model

The orchestrator is deterministic application code. It owns route selection, task scheduling, retries, validation, ledger writes, and approvals. It is **not** an LLM super-agent.

```text
approved source event
  → raw artifact vault
  → deterministic route
  → bounded ADK evidence agent
  → schema/provenance/privacy validation
  → entity + case proposal
  → deterministic ledger update
  → Delta Investigator
  → Quality/Safety Review
  → staged case
  → human approval
  → Inquiry Planner / Brief Builder
  → deterministic draft-packet renderer
```

Do not let any agent browse freely, query the full corpus, call email/CMS/forms, change Firestore directly, or self-delegate in an unbounded loop.

## 7. Repository Rules

- Put backend code under `backend/`, frontend code under `frontend/`, and infrastructure under `infra/`.
- Keep architecture/product decisions in `docs/`; do not duplicate the PRD inside code comments.
- Version prompts and schemas in code, then link to the detailed design doc.
- Keep only reviewed public fixtures under `backend/tests/fixtures/`; never commit personal/restricted data.
- Do not commit `.env`, credentials, source caches, service-account JSON, raw non-fixture media, or Terraform state.
- Never make console-only cloud changes without recording them in IaC or documenting a temporary exception.

## 8. Definition of Done for the MVP

The MVP is done when a reviewed City of Milwaukee replay corpus runs end to end in a deployed Cloud environment and produces one source-cited Decision Delta plus a human-approved inquiry packet. It must visibly preserve raw artifacts, handle a duplicate event once, represent a missing attachment explicitly, demonstrate a failed approval attempt, and expose trace/job lineage in Google Cloud.

## 9. First Instruction for a New Claude Code Session

Read this file and these documents: `CONTEXT.md`, `docs/product/PRD.md`, `docs/architecture/multi-agent-design-and-prompts.md`, `docs/architecture/google-agent-stack-decision.md`, `docs/implementation/project-structure.md`, `docs/implementation/reasoning-visibility-ux.md`, and `.claude/rules/privacy-and-evidence.md`. Then use plan mode to propose **only** the first City source-replay vertical slice, including files, tests, local setup, and acceptance criteria. Do not write code until the plan is approved.

## Agent skills

### Issue tracker

Three places, one rule: Linear (team `Moodyco`, via `/linear-build`) for planned build work; local markdown under `.scratch/<feature>/` for scratch/solo work; GitHub Issues (`gh`) once this repo has a GitHub remote. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context. `CONTEXT.md` at the repo root, ADRs in `docs/adr/`; `docs/decisions/` stays the plain-English portfolio log. See `docs/agents/domain.md`.

# Clean Code Standards

All code produced in this project must follow these clean code principles. These are non-negotiable defaults — not suggestions.

## Naming

- Every variable, function, and class name must clearly communicate its purpose. No single-letter names, no abbreviations unless universally understood (e.g., `id`, `url`).
- Use `numberOfUsers` not `n`. Use `calculateShippingCost` not `calc`.

## Functions

- Each function does ONE thing (Single Responsibility Principle). If you can describe what a function does using "and," split it.
- Keep functions under 20 lines. If longer, extract helper functions.
- Prefer small, composable functions over large monolithic ones.

## Comments

- Code should be self-explanatory. Comments explain WHY, never WHAT or HOW.
- Bad: `// Loop through users` — Good: `// Retry failed users from the last sync batch`
- Delete comments that restate the code. Outdated comments are worse than no comments.

## Formatting & Consistency

- Use consistent indentation (2 or 4 spaces — pick one, never mix).
- Group related logic with blank lines. Separate concerns visually.
- Use Prettier/ESLint or equivalent formatter. Every file should look like the same person wrote it.

## No Hardcoded Values

- Extract magic numbers and strings into named constants or config.
- Bad: `if (users >= 100)` — Good: `if (users >= MAX_USERS)`

## Project Structure

- Organize by concern: `components/`, `services/`, `utils/`, `tests/`.
- Keep test files outside `src/` in a mirrored structure.
- Never dump everything in one directory.

## Error Handling

- Fail fast. Throw meaningful errors with clear messages.
- Use try/catch blocks. Never silently swallow errors.
- Log like you're documenting a crime scene: precise, relevant, minimal.

## Testing

- Write unit tests for every function with logic.
- Tests should be as clean as production code.
- Test edge cases, not just the happy path.

## Dependency Injection

- Pass dependencies as arguments rather than hardcoding them.
- This makes code testable and swappable.

## The Boy Scout Rule

- Leave every file cleaner than you found it.
- When touching existing code: rename unclear variables, extract messy functions, remove dead code.

## Open/Closed Principle

- Design for extension, not modification. Use polymorphism and composition.
- Adding a new feature should not require rewriting existing working code.

## Code Smells to Fix on Sight

- Duplicated logic → extract into a shared function
- God objects doing everything → split responsibilities
- Long parameter lists → use an options/config object
- Nested conditionals 3+ levels deep → extract or invert early returns
