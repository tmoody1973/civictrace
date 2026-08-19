# CivicTrace Complete Project Structure

## Repository Layout

```text
civictrace/
├── README.md                               # Product overview, setup, demo path, documentation index.
├── CLAUDE.md                               # Short, always-loaded Claude Code operating contract.
├── .env.example                            # Non-secret local environment variables and guardrail defaults.
├── .gitignore                              # Blocks secrets, raw source caches, generated media, and local state.
├── pyproject.toml                          # Python workspace/lint/test configuration; create before backend coding.
├── package.json                            # Frontend workspace scripts; create before frontend coding.
├── docker-compose.yml                      # Local-only emulators/dependencies; optional, never production source of truth.
│
├── .claude/
│   ├── rules/
│   │   ├── gcp-operations.md               # Cost, IAM, lifecycle, deploy, and teardown guardrails.
│   │   └── privacy-and-evidence.md         # Evidence provenance, MPS data, neutral language, approval boundary.
│   ├── skills/
│   │   └── gcp-ops-review/SKILL.md         # Read-only pre-deploy/cloud change review procedure.
│   └── agents/
│       └── gcp-ops-reviewer.md             # Restricted infrastructure-review subagent.
│
├── docs/
│   ├── README.md                            # Documentation index.
│   ├── product/PRD.md                       # Product source of truth.
│   ├── architecture/
│   │   ├── multi-agent-design-and-prompts.md
│   │   ├── google-agent-stack-decision.md
│   │   ├── civictrace-architecture.mmd
│   │   ├── civictrace-architecture.png
│   │   ├── promise-ledger-flow.mmd
│   │   └── promise-ledger-flow.png
│   ├── implementation/
│   │   ├── project-structure.md             # This file.
│   │   ├── backend-adk-outline.md           # Python ADK package, models, and orchestration outline.
│   │   └── api-contract.md                  # HTTP/event contracts; create before API work.
│   ├── integrations/api-stack-and-vendor-decision.md
│   ├── research/
│   │   ├── milwaukee-go-no-go.md
│   │   └── mps-meeting-monitor-and-expansion.md
│   ├── sources/
│   │   ├── source-allowlist.example.yaml
│   │   ├── corpus-manifest.example.yaml
│   │   ├── source-allowlist.yaml            # Environment-reviewed copy; do not add source silently.
│   │   └── corpus-manifest.yaml             # Reviewed replay corpus; no restricted data.
│   ├── evaluations/README.md
│   ├── runbooks/
│   │   ├── cost-security-and-claude-code.md
│   │   ├── deploy.md
│   │   └── demo-teardown.md
│   ├── hackathon/
│   │   ├── official-requirements.md
│   │   ├── prize-competition-blueprint.md
│   │   └── demo-and-repo-plan.md
│   └── adr/
│       ├── ADR-001-adk-python-vertex.md     # Record framework choice; create from Google stack decision.
│       └── ADR-002-evidence-and-approval-boundary.md
│
├── backend/
│   ├── README.md                            # Local backend setup, test commands, dependency boundaries.
│   ├── pyproject.toml                       # Python dependencies: ADK, FastAPI, Pydantic, GCP clients, test tools.
│   ├── app/
│   │   ├── main.py                          # FastAPI app assembly, router registration, health endpoint.
│   │   ├── core/
│   │   │   ├── config.py                    # Typed environment settings; prohibit unsafe defaults.
│   │   │   ├── logging.py                   # Structured trace/job logging.
│   │   │   ├── dependencies.py              # FastAPI dependency providers.
│   │   │   └── ids.py                       # Stable IDs and idempotency-key helpers.
│   │   ├── domain/
│   │   │   ├── enums.py                     # Job, source, evidence, case, approval state machines.
│   │   │   ├── models.py                    # Pure domain objects; no FastAPI/GCP imports.
│   │   │   └── errors.py                    # Typed domain exceptions.
│   │   ├── schemas/
│   │   │   ├── source.py                    # Pydantic contracts for sources/events/artifacts.
│   │   │   ├── evidence.py                  # Anchors, extracted evidence, commitments, meeting facts.
│   │   │   ├── case.py                      # Cases, links, Decision Delta contracts.
│   │   │   ├── review.py                    # Quality reviews, approvals, inquiry/brief drafts.
│   │   │   └── api.py                       # Public request/response envelopes.
│   │   ├── policies/
│   │   │   ├── global_policy.py             # Shared LLM policy contract string/version.
│   │   │   ├── source_policy.py             # Domain/path/content-type allowlist enforcement.
│   │   │   ├── evidence_policy.py           # Anchor/claim completeness validation.
│   │   │   ├── privacy_policy.py            # MPS/student-data deny rules and content filters.
│   │   │   └── approval_policy.py           # Approval-token restrictions and expiry rules.
│   │   ├── repositories/
│   │   │   ├── artifacts.py                 # Artifact metadata, hash, GCS pointer persistence.
│   │   │   ├── cases.py                     # Firestore case + append-only ledger operations.
│   │   │   ├── jobs.py                      # Job state, idempotency, dead-letter/replay records.
│   │   │   ├── approvals.py                 # Approval token/event persistence.
│   │   │   └── corrections.py               # Human correction persistence and retrieval.
│   │   ├── services/
│   │   │   ├── artifact_vault.py            # GCS save/read/hash and source metadata.
│   │   │   ├── retrieval.py                 # Bounded case/corpus retrieval; BigQuery prefilter.
│   │   │   ├── validator.py                 # Schema, source anchor, PII, policy, and transition validation.
│   │   │   ├── approval_service.py          # Human approval event and token verification.
│   │   │   ├── packet_renderer.py           # Deterministic inquiry packet rendering.
│   │   │   └── speech.py                    # STT batch submission/polling; P1 only.
│   │   ├── tools/
│   │   │   ├── artifact_tools.py            # Read-only ADK tools for bounded artifact excerpts/anchors.
│   │   │   ├── case_tools.py                # Read-only case/evidence bundle tools.
│   │   │   └── entity_tools.py              # Read-only candidate entity/correction tools.
│   │   ├── agents/
│   │   │   ├── prompts.py                   # Versioned global policy plus role prompts.
│   │   │   ├── factory.py                   # ADK Agent construction; no state mutation tools.
│   │   │   ├── document_evidence.py         # A2 wrapper/structured result translation.
│   │   │   ├── media_evidence.py            # A3 wrapper; no voice identity logic.
│   │   │   ├── entity_resolution.py         # A4 wrapper.
│   │   │   ├── case_linker.py               # A5 wrapper.
│   │   │   ├── delta_investigator.py        # A6 wrapper.
│   │   │   ├── quality_reviewer.py          # A7 wrapper.
│   │   │   ├── inquiry_planner.py           # A8 wrapper.
│   │   │   └── brief_builder.py             # A9 wrapper.
│   │   ├── orchestration/
│   │   │   ├── routes.py                    # Deterministic MIME/source route registry.
│   │   │   ├── state_machine.py             # Allowed job/case transitions.
│   │   │   ├── workflow.py                  # Bounded event-to-staged-case workflow.
│   │   │   └── idempotency.py               # Stable dedupe key and duplicate suppression.
│   │   ├── events/
│   │   │   ├── publisher.py                 # Pub/Sub publish abstraction.
│   │   │   └── handlers.py                  # Event decode/validate/dispatch only.
│   │   ├── workers/
│   │   │   ├── task_handler.py              # Internal Cloud Tasks endpoint.
│   │   │   ├── source_watch.py              # Scheduler/direct adapter trigger.
│   │   │   ├── extraction.py                # Artifact → agent route job.
│   │   │   ├── case_update.py               # Validated proposals → ledger update.
│   │   │   └── artifact_render.py           # Valid approval → deterministic packet output.
│   │   └── api/
│   │       ├── routes_health.py             # Liveness/readiness only.
│   │       ├── routes_cases.py              # Read cases/timeline/evidence endpoints.
│   │       ├── routes_review.py             # Corrections/approval request endpoints.
│   │       ├── routes_sources.py            # Developer/admin source status; no hidden source add.
│   │       └── routes_tasks.py              # IAM-authenticated internal worker route.
│   ├── tests/
│   │   ├── unit/                            # Validators, policies, idempotency, state transitions.
│   │   ├── integration/                     # Adapter → vault → task → ledger paths with fakes/emulators.
│   │   ├── evaluations/                     # Grounding, missingness, conflict, privacy, approval suites.
│   │   └── fixtures/                        # Reviewed public replay artifacts + manifests only.
│   └── scripts/
│       ├── replay_corpus.py                 # Submit reviewed fixture manifest to local/demo pipeline.
│       └── seed_dev.py                      # Developer-only known fixture state; never production data.
│
├── frontend/
│   ├── README.md                            # Frontend setup and Evidence Studio principles.
│   ├── package.json                         # Next.js, React, shadcn/ui, Kibo UI, TanStack Table, PDF/media deps.
│   ├── tailwind.config.ts                   # CivicTrace design tokens.
│   └── src/
│       ├── app/                             # Next.js routes/layouts.
│       ├── components/
│       │   ├── layout/                      # App shell, sidebar, top bar, responsive panels.
│       │   ├── evidence/                    # PDF/media inspector, anchor/highlight, timeline/graph.
│       │   ├── case/                        # Promise card, Decision Delta, case rail.
│       │   ├── meeting/                     # Transcript, media controls, brief preview.
│       │   └── ui/                          # Local wrappers around shadcn/Kibo components only.
│       ├── features/                        # Query/mutation hooks and domain views by user workflow.
│       ├── lib/                             # Typed API client, auth, formatting, feature flags.
│       └── types/                           # Frontend copies of public API contracts/generated types.
│
├── infra/
│   ├── README.md                            # IaC and environment principles.
│   ├── terraform/
│   │   ├── modules/                         # Cloud Run, GCS, Firestore, Pub/Sub, Tasks, Scheduler, BQ, IAM, budgets.
│   │   └── environments/
│   │       ├── dev/                         # Local/development GCP environment variables.
│   │       └── demo/                        # Capped, labeled hackathon demo environment.
│   └── scripts/                             # Read-only guardrail/resource inventory helpers.
│
├── scripts/
│   ├── verify-cloud-guardrails.sh           # Read-only predeploy policy check; create after IaC exists.
│   ├── deploy-demo.sh                       # Explicit-human-confirm deploy helper; create after IaC exists.
│   ├── cost-status.sh                       # Read-only cost/resource posture summary.
│   └── demo-teardown.sh                     # Label-targeted cleanup; requires explicit confirmation.
│
└── .github/workflows/
    ├── backend-ci.yml                       # Unit, integration, evaluation tests, lint/type checks.
    ├── frontend-ci.yml                      # Type checks, lint, build, accessibility/smoke checks.
    └── infra-plan.yml                       # Plan-only IaC checks; no automatic production apply.
```

## Module Rules

The backend maintains a strict dependency direction. `domain` and `schemas` cannot import FastAPI, ADK, Firestore, or Cloud clients. `agents` receive only read-only tools and produce typed proposals. `orchestration` invokes agents and validators but never lets an agent mutate Firestore directly. `workers` execute deterministic handlers from a task/event; they do not accept unbounded browser/user input.

The frontend owns evidence inspection and human review. It never receives model-provider keys, service-account credentials, raw queue endpoints, or write access to source/artifact stores. It calls authenticated API routes that return source-anchored, typed data.

## File Creation Order

Create only the P0 files required for the Milwaukee City replay loop first: backend configuration, domain/enums, source/evidence/case schemas, direct Legistar adapter, artifact vault, document agent, validator, deterministic workflow, task handler, case/review API routes, one Evidence Studio page, and the grounding/idempotency/missingness/approval tests. Do not scaffold every source adapter or UI page as empty boilerplate.
