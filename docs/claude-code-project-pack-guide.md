# CivicTrace Claude Code Project Documentation Pack

## Purpose

This guide answers a practical question: **which materials from the CivicTrace work should enter the repository, where should they live, and which files should Claude Code read automatically versus only when relevant?**

The answer is to create a curated project pack—not to copy every research note into the root directory. The repository should give Claude Code clear, durable product context without loading pages of historical brainstorming into every task.

> **Rule of thumb:** Keep the project’s current product truth, technical contracts, safety rules, and implementation runbooks. Archive early idea exploration, scoring scripts, and superseded concept work outside the active repository context.

---

## 1. Recommended Project Structure

```text
civictrace/
├── README.md
├── CLAUDE.md
├── .env.example
├── .gitignore
│
├── .claude/
│   ├── settings.json
│   ├── rules/
│   │   ├── gcp-operations.md
│   │   └── privacy-and-evidence.md
│   ├── skills/
│   │   └── gcp-ops-review/
│   │       └── SKILL.md
│   └── agents/
│       └── gcp-ops-reviewer.md
│
├── docs/
│   ├── README.md
│   ├── product/
│   │   └── PRD.md
│   ├── architecture/
│   │   ├── multi-agent-design-and-prompts.md
│   │   ├── google-agent-stack-decision.md
│   │   ├── civictrace-architecture.mmd
│   │   ├── civictrace-architecture.png
│   │   ├── promise-ledger-flow.mmd
│   │   └── promise-ledger-flow.png
│   ├── integrations/
│   │   └── api-stack-and-vendor-decision.md
│   ├── research/
│   │   ├── milwaukee-go-no-go.md
│   │   └── mps-meeting-monitor-and-expansion.md
│   ├── hackathon/
│   │   ├── official-requirements.md
│   │   ├── prize-competition-blueprint.md
│   │   └── demo-and-repo-plan.md
│   ├── runbooks/
│   │   ├── cost-security-and-claude-code.md
│   │   ├── deploy.md
│   │   └── demo-teardown.md
│   ├── decisions/
│   │   └── ADR-001-use-adk-python-and-vertex-ai.md
│   ├── evaluations/
│   │   └── README.md
│   └── sources/
│       ├── source-allowlist.example.yaml
│       └── corpus-manifest.example.yaml
│
├── infra/
│   ├── README.md
│   └── terraform/                 # create when implementation begins
├── scripts/
│   ├── README.md
│   ├── verify-cloud-guardrails.sh # create when implementation begins
│   ├── deploy-demo.sh             # create when implementation begins
│   └── demo-teardown.sh           # create when implementation begins
└── src/                            # application code begins here
```

---

## 2. Existing Documents to Copy Into the Project

### Essential product, architecture, and build documents

These are the current source of truth. Copy them into the stated location and retain their references/links.

| Existing conversation artifact | Destination in project | Why it belongs | When Claude Code should read it |
|---|---|---|---|
| `CivicTrace_Comprehensive_PRD_and_Project_Proposal.md` | `docs/product/PRD.md` | Full product definition: users, requirements, scope, data model, safety boundary, technical architecture, rollout, and project proposal. | Before any material product or data-model change. |
| `CivicTrace_Multi_Agent_Architecture_and_Prompts.md` | `docs/architecture/multi-agent-design-and-prompts.md` | Canonical agent roles, system prompts, structured outputs, validation gates, approval model, and tests. | Before implementing/changing agents, agent tools, schemas, or workflow state. |
| `CivicTrace_Google_Agent_Stack_Decision.md` | `docs/architecture/google-agent-stack-decision.md` | Explains ADK/Python/Vertex AI decision and responsibility of each Google service. | Before framework, deployment, or service-boundary changes. |
| `CivicTrace_API_Stack_and_Vendor_Recommendation.md` | `docs/integrations/api-stack-and-vendor-decision.md` | Direct source adapters and explicit go/no-go policy for TinyFish/Parallel and external APIs. | Before adding any external API, scraper, crawler, or vendor. |
| `Milwaukee_CivicTrace_Go_No_Go.md` | `docs/research/milwaukee-go-no-go.md` | Pilot-city decision, official source backbone, product boundary, and selected initial workflow. | Before changing Milwaukee source scope or pitch. |
| `CivicTrace_Meeting_Monitor_and_MPS_Expansion.md` | `docs/research/mps-meeting-monitor-and-expansion.md` | MPS adapter scope, meeting-transcript system, privacy boundary, public-procurement guidance. | Before implementing the meeting monitor or MPS capability. |
| `CivicTrace_Prize_Requirements.md` | `docs/hackathon/official-requirements.md` | Scoring logic, required stack, submission constraints, prize limitation. | Before changing demo scope or writing Devpost submission. |
| `CivicTrace_Prize_Competition_Blueprint.md` | `docs/hackathon/prize-competition-blueprint.md` | Explicit strategy for Taskmaster, architecture, and multimodal UX competitiveness. | Before demo design, UI polish, or submission writing. |
| `CivicTrace_Demo_and_Repo_Plan.md` | `docs/hackathon/demo-and-repo-plan.md` | Four-minute demo structure and repository proof checklist. | Before feature freeze, recording, or writing README. |
| `CivicTrace_Claude_Code_Cost_Security_Guide.md` | `docs/runbooks/cost-security-and-claude-code.md` | The full rationale for Claude rules, IaC enforcement, cost controls, identity, and teardown. | Before deploy, infrastructure work, budgets, or teardown. |

### Essential visuals

| Existing conversation artifact | Destination in project | Why it belongs |
|---|---|---|
| `civictrace_competition_architecture.mmd` | `docs/architecture/civictrace-architecture.mmd` | Editable architecture source for docs, pitch, and demo. |
| `assets/civictrace_competition_architecture.png` | `docs/architecture/civictrace-architecture.png` | Rendered architecture visual for README/Devpost. |
| `civictrace_promise_ledger_flow.mmd` | `docs/architecture/promise-ledger-flow.mmd` | Editable product workflow source. |
| `assets/civictrace_promise_ledger_flow.png` | `docs/architecture/promise-ledger-flow.png` | Rendered product/evidence workflow visual. |

### Useful but optional reference material

Keep these in `docs/research/archive/` only if you want the original supporting evidence immediately available in the project. The PRD and main research documents already synthesize their conclusions.

| Existing artifact | Recommendation |
|---|---|
| `milwaukee_civictrace_research.md` | Optional: copy to `docs/research/archive/milwaukee-source-validation.md`. |
| `mps_civictrace_research.md` | Optional: copy to `docs/research/archive/mps-source-validation.md`. |
| `official_overview_notes.md` | Optional: copy to `docs/hackathon/archive/official-notes.md`. The requirements document is the active summary. |
| `city_selection_notes.md` / `city_candidate_summary.md` | Archive only if you need to defend Milwaukee vs. San Francisco/Chicago later. |

---

## 3. Materials **Not** to Put in the Active CivicTrace Project

Do not copy old, superseded exploration into the repository’s active documentation tree. It creates confusion for both humans and Claude Code.

| Existing artifact group | Why to leave it out |
|---|---|
| `Afterlight_Hackathon_Win_Strategy.md`, `afterlight_architecture.mmd`, `assets/afterlight_architecture.png` | This is the discarded disaster-recovery concept, not CivicTrace. |
| `fieldwater_opportunity_notes.md` | Superseded water-operations idea. |
| `concept_options.md`, `concept_scorecard.md`, `category_creating_opportunities.md`, `sector_candidate_comparison.md`, `civictrace_selection.md` | Historical ideation/selection record; useful only outside the implementation repo. |
| `score_concepts.py`, `summarize_city_candidates.py`, `summarize_sector_scan.py` | Temporary analysis scripts, not CivicTrace product code. |
| Raw map/parallel subtask CSV/JSON files | Research-process artifacts, not curated evidence or product fixtures. |

If you want to preserve this history, create a separate private folder outside the code repository: `civictrace-strategy-archive/`.

---

## 4. Files You Still Need to Create

The conversation generated the product knowledge; it did **not** generate the implementation repository. These files turn the docs into a buildable project.

| File | Purpose | Required before coding? |
|---|---|---:|
| `README.md` | Project overview, local setup, architecture, screenshots, demo path, and how to run tests. | Yes |
| `CLAUDE.md` | Short, always-loaded CivicTrace rules and pointers to the detailed docs. | Yes |
| `.env.example` | Non-secret local environment-variable template. | Yes |
| `.gitignore` | Blocks `.env`, service-account keys, source caches, local media, generated artifacts, and Claude local settings. | Yes |
| `.claude/rules/gcp-operations.md` | Detailed cost/security/deployment rules. | Yes |
| `.claude/rules/privacy-and-evidence.md` | Public-source, provenance, MPS privacy, and external-action rules. | Yes |
| `docs/sources/source-allowlist.example.yaml` | Makes source domains/adapters explicit from day one. | Yes |
| `docs/sources/corpus-manifest.example.yaml` | Defines replayable demo corpus and expected artifacts. | Yes |
| `docs/evaluations/README.md` | Lists grounding, idempotency, missingness, conflict, and approval tests. | Yes |
| `infra/README.md` | States environment design, resource-label rules, and IaC workflow. | Yes |
| `docs/runbooks/deploy.md` | Human-controlled deployment procedure. | Before first deployment |
| `docs/runbooks/demo-teardown.md` | Safe cleanup after demo and submission. | Before first deployment |
| `scripts/verify-cloud-guardrails.sh` | Checks caps, auth, retention, secrets, and environment labels. | Before deploy |
| Application code under `src/` | ADK service, source adapters, workers, UI, tests, and infrastructure. | This is the next build phase |

---

## 5. What Belongs in `CLAUDE.md` vs. Reference Docs

`CLAUDE.md` should be a navigation and policy layer, not a duplicate PRD. It should remain concise enough to be read every session.

| Put directly in `CLAUDE.md` | Keep in docs and reference only when needed |
|---|---|
| Product sentence and current MVP scope. | Full PRD narrative and user personas. |
| Non-negotiable evidence, privacy, approval, and deployment rules. | Full agent prompts and schemas. |
| ADK/Python + Vertex AI decision. | Service-by-service architecture explanation. |
| Links to the 5–7 docs that must be read before relevant work. | Research evidence, source notes, pitch language. |
| Instruction to use plan mode before infrastructure, data-policy, or agent-boundary changes. | Detailed runbooks and test fixtures. |

### Minimum `CLAUDE.md` reading map

```md
Before doing work, read the relevant project document:

- Product scope/data model: `docs/product/PRD.md`
- Agent implementation or prompts: `docs/architecture/multi-agent-design-and-prompts.md`
- Google Cloud/ADK architecture: `docs/architecture/google-agent-stack-decision.md`
- External sources/APIs: `docs/integrations/api-stack-and-vendor-decision.md`
- Milwaukee/MPS scope: `docs/research/`
- Demo/submission: `docs/hackathon/`
- Cost/security/deploy: `.claude/rules/gcp-operations.md` and `docs/runbooks/`
```

---

## 6. Recommended Copy Order

1. Create an empty `civictrace/` repository.
2. Copy the ten essential Markdown documents and four diagram assets into the destinations above.
3. Add the new root/Claude Code scaffolding documents listed in Section 4.
4. Open Claude Code in the repository and ask it to read `CLAUDE.md`, then create a detailed implementation plan for **only the Milwaukee City direct-source replay loop**.
5. Do not start MPS, TinyFish, Parallel, publishing integrations, or live procurement crawling until the City loop passes its evidence-grounding, duplicate-event, missing-source, and approval-gate tests.

---

## 7. Definition of a Healthy Starting Repository

Before implementation begins, a healthy CivicTrace repository contains the current product truth, a short Claude Code instruction file, a fully defined safety boundary, direct source policies, a replay corpus plan, editable diagrams, and a clear test/evaluation plan. It does **not** contain stale concepts, secrets, copied vendor documentation, uncurated data dumps, or a giant global instruction file.

