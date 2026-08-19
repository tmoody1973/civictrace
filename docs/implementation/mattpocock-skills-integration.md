# Using `mattpocock/skills` with CivicTrace

## Decision

Install the external skills **once**, then treat the CivicTrace starter as the source of truth for product, safety, architecture, and project-specific operating rules. Do not copy the whole `mattpocock/skills` repository into this repository manually. The external skills provide reusable engineering workflow; CivicTrace supplies the domain constraints that the workflow must obey.

The upstream repository offers two mutually exclusive approaches: a managed Claude Code plugin that is read-only and updates automatically, or an editable project-local installation through `skills.sh`.[1] For CivicTrace, use the **managed Claude Code plugin** unless you intend to modify the upstream skills themselves. Do not install both approaches, because the upstream project warns that this duplicates every skill.[1]

---

## One-time setup

### Step 1: Unzip and enter the CivicTrace starter

```bash
unzip civictrace_claude_code_starter_updated.zip
cd civictrace_claude_code_starter
```

If this is a new repository, initialize Git and make a first documentation commit before implementation begins.

```bash
git init
git add .
git commit -m "docs: add CivicTrace project contract and implementation plan"
```

### Step 2: Install the external skills, choosing one route

**Recommended: managed Claude Code plugin**

```text
/plugin install mattpocock-skills
```

The command above is the official in-session installation method. The CLI alternative is `claude plugins install mattpocock-skills`.[1]

**Alternative: editable local skills**

```bash
npx skills@latest add mattpocock/skills
```

Select only the skills in the table below, target Claude Code, and include `setup-matt-pocock-skills`. Use this only if you need to edit the imported external skill files. Do **not** also install the managed plugin.[1]

### Step 3: Configure the external workflow

Inside Claude Code, run:

```text
/setup-matt-pocock-skills
```

When it asks where documents should be stored, select or enter **`docs/engineering`**. When it asks for an issue tracker, choose:

| Situation | Select | Why |
|---|---|---|
| You already use GitHub Issues for the hackathon project | **GitHub** | Keeps source code, work tickets, review, and deploy proof together. |
| You have a working Linear workspace and want team planning | **Linear** | Use only if it is already part of your team's actual workflow. |
| You are working solo before a remote repository exists | **Local files** | Fastest zero-setup path; migrate only if needed. |

Recommended labels if it asks for triage labels:

```text
kind:spec, kind:task, kind:bug, area:backend, area:frontend,
area:infra, risk:privacy, risk:source-policy, scope:mvp, source:milwaukee
```

### Step 4: Keep the context hierarchy clear

Use the documents in this order:

1. **`CLAUDE.md`** is the always-on operating contract and product boundary.
2. **`CONTEXT.md`** is the shared vocabulary for skills such as domain modeling, specs, tickets, and code review.
3. **`.claude/rules/`** holds mandatory security, privacy, evidence, and cloud operations rules.
4. **`docs/`** holds the detailed PRD, architecture, sources, research, runbooks, specs, tickets, and decisions.
5. **External skills** control _how_ Claude Code plans, implements, tests, reviews, and hands off work. They do not override items 1–4.

---

## Recommended skill set for CivicTrace

| External skill | When to invoke it | CivicTrace input | Expected artifact/outcome |
|---|---|---|---|
| `/setup-matt-pocock-skills` | Once per repository | Tracker/doc preference | Engineering workflow configuration. |
| `/grill-with-docs` | Before a new feature or material design decision | Relevant `CLAUDE.md`, `CONTEXT.md`, and smallest relevant source docs | Clarified vocabulary, questions, ADR/spec updates. |
| `/to-spec` | After a decision is settled | The conversation plus source docs | A narrow specification, stored under `docs/engineering/specs/`. |
| `/to-tickets` | After a spec is accepted | The spec | Small blocked/unblocked work items, each with tests and acceptance criteria. |
| `/implement` | For exactly one accepted ticket/slice | Ticket + tests + architecture docs | Small vertical implementation, no broad scaffolding. |
| `/tdd` | During every behavior-changing implementation | Ticket acceptance criteria + fixtures | Red-green-refactor loop and regression tests. |
| `/code-review` | Before a commit/PR | The diff and originating spec/ticket | Standards and spec-fidelity review. |
| `/research` | For third-party API, Google Cloud, Milwaukee, MPS, or legal/source-policy questions | A narrowly framed question | Cited Markdown evidence under `docs/research/`. |
| `/domain-modeling` | When terms/schemas drift | `CONTEXT.md`, schemas, fixture examples | Shared-language and naming updates. |
| `/codebase-design` | Before adding a cross-cutting module | Existing module boundaries | A deep module design at a clean seam. |
| `/diagnosing-bugs` | When test/debugging feedback is unclear | Reproducible failing case | Instrumented diagnosis and regression test. |
| `/wizard` | When a human must configure GCP, secrets, billing, or external console settings | Runbook and user-owned account | A human-run, non-destructive setup guide. |
| `/improve-codebase-architecture` | Every few days once code exists | Current repository state | Candidate architectural improvements; do not run as a rescue after a rushed build. |

The upstream skill collection distinguishes user-invoked orchestration skills from reusable model-invoked disciplines; its engineering list includes the spec, ticket, implementation, TDD, research, domain-modeling, review, and diagnostic workflows mapped above.[1]

---

## The First CivicTrace Session

Start a new Claude Code session from the repository root and use this sequence.

```text
1. Read CLAUDE.md, CONTEXT.md, docs/product/PRD.md,
   docs/architecture/multi-agent-design-and-prompts.md,
   docs/architecture/google-agent-stack-decision.md,
   docs/implementation/project-structure.md,
   docs/implementation/reasoning-visibility-ux.md, and
   .claude/rules/privacy-and-evidence.md.

2. Enter plan mode. Propose only the City source-replay vertical slice:
   approved fixture → artifact vault → deterministic extraction-validation boundary →
   one Evidence Trace API response.

3. Run /grill-with-docs if the scope, source, domain language, schema, or acceptance criteria
   remain ambiguous. Do not code until the slice is approved.

4. Run /to-spec. Save the result in docs/engineering/specs/.

5. Run /to-tickets. The first ticket must be a small, independently testable slice.

6. Run /implement for the first ticket. Require /tdd at each behavior-changing seam.

7. Run /code-review before committing. Verify every material claim/trace step has an anchor.
```

### First slice definition

The first slice should **not** invoke Gemini, deploy Cloud Run, or scrape a live City site. It should process one reviewed local fixture and prove four non-negotiable states:

| Test case | Required result |
|---|---|
| Valid source event | Immutable artifact metadata and deterministic evidence-extraction proposal. |
| Duplicate source event | Suppressed before a second durable result. |
| Missing attachment | `NOT_PUBLISHED` ledger and Evidence Trace state, not failure or invented conclusion. |
| Source anchor | Trace API response links the validated evidence to the fixture page/row/field. |

Only after that slice passes should the next spec introduce bounded ADK invocation and typed agent outputs.

---

## CivicTrace-specific guardrails to repeat during every skill flow

Paste this reminder into a skill session when the task affects source evidence, agents, MPS, infrastructure, or UI:

```text
CivicTrace guardrails:
- Read CLAUDE.md and CONTEXT.md first.
- Evidence before prose; every material claim must retain exact public-source anchors.
- Unknown stays UNKNOWN, NOT_PUBLISHED, CONFLICTING, CANDIDATE_LINK, REQUEST_NEEDED, or HUMAN_REVIEW.
- Agents return typed proposals only; deterministic code validates and writes state.
- No model-controlled approval, publication, outreach, records request, browsing, or Firestore mutation.
- MPS scope is public institutional/aggregate information only; reject individual student data.
- Use the AI SDK Elements ChainOfThought component only as an Evidence Trace of ledger/validator events, never raw private model reasoning.
- Cloud/integration changes require plan mode, fixtures, cost review, and a human approval boundary.
```

---

## Directory additions created by the external workflow

Create these directories when first needed. Do not prefill them with generic boilerplate.

```text
docs/
  engineering/
    specs/           # Accepted small-slice specifications
    tickets/         # Local ticket files if no issue tracker is selected
    decisions/       # ADRs from grill-with-docs/domain-modeling
    reviews/         # Durable architecture/review reports when they inform later work
```

Do not move the current PRD, technical architecture, runbooks, or source policy into `docs/engineering`. They are project truth already located under `docs/product`, `docs/architecture`, `docs/sources`, and `docs/runbooks`.

---

## What not to do

- Do not install both the managed plugin and editable local skill files.
- Do not let an external skill overwrite `CLAUDE.md`, `CONTEXT.md`, source policy, privacy rules, or the MVP boundary without explicit review.
- Do not use `/implement` against an unreviewed “build the whole app” ticket.
- Do not write generic tickets such as “Build agents” or “Set up GCP.” Each ticket must state the specific boundary, fixture, test, acceptance criteria, cost impact, and rollback/teardown impact.
- Do not connect a live public source, model, Cloud account, or MPS dataset merely because a workflow skill recommends moving forward. CivicTrace plan-mode and human-approval rules still control.

## References

[1]: https://github.com/mattpocock/skills "mattpocock/skills README and skill catalog"
