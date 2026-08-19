# CivicTrace: Where Cost, Security, and Deployment Controls Belong in Claude Code

## Short Answer

**Do not put the entire list in `CLAUDE.md`.** Put a short, non-negotiable summary there, then distribute the actual controls by function:

| Concern | Correct home | Why |
|---|---|---|
| Rules Claude must remember on every task | `CLAUDE.md` | Short project context and non-negotiable operating principles. |
| Detailed GCP cost/security/deployment instructions | `.claude/rules/gcp-operations.md` | Reusable, scoped project rules without bloating the root context file. |
| A repeatable “review our cloud setup” capability | `.claude/skills/gcp-ops-review/SKILL.md` | A deliberate capability you invoke when planning, deploying, reviewing cost, or tearing down. |
| A specialized reviewer with restricted tools | `.claude/agents/gcp-ops-reviewer.md` | Gives Claude Code a defined infrastructure-review role rather than letting every coding task alter cloud configuration. |
| Actual enforceable service limits | `infra/` infrastructure-as-code and CI policy checks | Prompts are guidance; IaC and CI make minimum/maximum instances, auth, retention, and budgets real. |
| Deployment/teardown commands | `scripts/` and `docs/runbooks/` | Commands must be versioned, reviewable, and runnable outside a chat session. |
| Developer-specific local values | `.claude/settings.local.json` and local `.env` files | Keep personal overrides/secrets out of shared Git history. |
| Claude Code tool permissions | `.claude/settings.json` | Allow/block tool calls and project environment configuration. |

Claude Code’s official project configuration separates `CLAUDE.md` project context from settings, skills, subagents, rules, workflows, and memory. Project files can be committed to Git for the team, while `~/.claude` is personal configuration. [1]

> **Core principle:** Put the *policy* in Claude instructions, the *implementation* in infrastructure-as-code, and the *proof/operations* in tests, scripts, CI, and runbooks.

---

## Recommended Repository Structure

```text
civictrace/
├── CLAUDE.md
├── .claude/
│   ├── settings.json
│   ├── settings.local.json          # gitignored; developer-specific only
│   ├── rules/
│   │   ├── gcp-operations.md
│   │   ├── privacy-and-evidence.md
│   │   └── release-safety.md
│   ├── skills/
│   │   └── gcp-ops-review/
│   │       └── SKILL.md
│   └── agents/
│       └── gcp-ops-reviewer.md
├── infra/
│   ├── terraform/                   # or Pulumi; choose one
│   ├── environments/
│   │   ├── dev.tfvars.example
│   │   └── demo.tfvars.example
│   └── policies/
│       └── validate_cost_security.sh
├── scripts/
│   ├── deploy-demo.sh
│   ├── cost-status.sh
│   ├── demo-teardown.sh
│   └── verify-cloud-guardrails.sh
├── docs/
│   ├── architecture.md
│   └── runbooks/
│       ├── deploy.md
│       ├── cost-control.md
│       ├── incident-and-recovery.md
│       └── demo-teardown.md
├── .env.example
└── .gitignore
```

## 1. Keep `CLAUDE.md` Short and Directive

`CLAUDE.md` should contain the rules that matter in almost every session, plus pointers to the detailed rules. Do not paste multi-page deployment commands, pricing tables, credentials, or one-off troubleshooting notes into it.

### Copy-paste `CLAUDE.md` block

```md
# CivicTrace Project Instructions

## Product and Safety Boundary

CivicTrace is an approval-gated public-evidence system. It must preserve source provenance, explicit uncertainty, and human control over all external-facing actions. Never implement autonomous publication, outreach, records-request submission, or ingestion of student-level/sensitive personal data.

## Cloud and Cost Guardrails

Before changing Google Cloud architecture, deployment configuration, Terraform/Pulumi, CI, or service settings, read:

- `.claude/rules/gcp-operations.md`
- `.claude/rules/privacy-and-evidence.md`
- `docs/runbooks/cost-control.md`

Non-negotiable defaults:

1. Use Gemini Flash by default. Escalate to a more expensive model only when a benchmarked task requires it and document why.
2. All Cloud Run services default to `min_instances = 0` and have a finite `max_instances` value.
3. Prefer serverless/managed components; do not introduce always-on clusters or databases without explicit approval and a cost rationale.
4. Treat security as configuration, not a comment: authenticated endpoints, least-privilege service accounts, Secret Manager, and no secrets in Git.
5. Infrastructure changes must go through `infra/` and pass `scripts/verify-cloud-guardrails.sh`.
6. Before recording the demo, run the cost/security checklist. After the demo, follow `docs/runbooks/demo-teardown.md`.

## Development Workflow

Use plan mode before infrastructure changes. Keep Terraform/Pulumi, application code, and docs in the same change set. Add/update tests when changing an agent, source adapter, access boundary, or deployment configuration.
```

---

## 2. Put the Detailed Operating Rules in `.claude/rules/gcp-operations.md`

This file is where your exact seven pro tips belong. It is detailed enough to guide Claude Code, but keeps the core product context clean.

### Copy-paste `.claude/rules/gcp-operations.md`

```md
# Google Cloud Operations Rules

Apply these rules whenever planning, implementing, reviewing, deploying, or debugging CivicTrace services on Google Cloud.

## Model and AI Spend

- Default to Gemini Flash for extraction, classification, routing, structured output, and normal case comparison.
- Do not use a more expensive model unless the task has a documented quality failure on Flash, a bounded benchmark shows the improvement, and the code includes an explicit model-selection reason.
- Never send the whole corpus to a model. Filter structured data first, retrieve only case-relevant source chunks, and cache artifact hashes, parsed text, and embeddings.
- Log model name, token usage where available, request class, and estimated cost per job. Do not log sensitive prompt content.

## Cloud Run Defaults

- Set minimum instances to 0 for every non-user-facing or demo service.
- Set a finite maximum instance limit for every service. Use the lowest viable CPU and memory configuration first.
- Set request and task timeouts deliberately; do not use unbounded retries or unbounded concurrency.
- Use Cloud Tasks/Pub/Sub to buffer bursty work instead of increasing always-on capacity.
- Do not deploy a public unauthenticated Cloud Run endpoint unless the specific endpoint is intentionally public, rate-limited, and documented in the threat model.

## Serverless Data and Storage

- Prefer BigQuery, Firestore, Cloud Storage, and serverless vector/retrieval options over dedicated always-on clusters for the hackathon MVP.
- Store raw evidence only when needed for provenance, replay, or approved retention. Compress eligible artifacts and use lifecycle policies for temporary media, parsed intermediates, and job artifacts.
- Store durable case state separately from temporary execution artifacts.
- Every storage bucket must have an owner, purpose, retention/lifecycle policy, and access policy documented in IaC.

## Budget and Billing Controls

- Configure budget alerts before nontrivial deployment. Document the project budget, alert thresholds, alert recipients, and a manual stop action in `docs/runbooks/cost-control.md`.
- Treat budget alerts as warnings, not automatic hard spending caps. Also enforce service-level max instances, queue concurrency limits, model budgets, and quota limits where available.
- Before a backfill, estimate expected artifact count, model calls, media minutes, and storage footprint. Start with a small bounded corpus and record actual usage.

## Endpoint and Identity Security

- Use least-privilege service accounts. One worker/service should not receive broad project-owner, storage-admin, or billing-admin permissions.
- Keep secrets in Secret Manager or local untracked environment files. Never commit API keys, service-account JSON, transcripts containing restricted data, or production credentials.
- Authenticate internal service-to-service calls. Use Cloud Run IAM, service identity, or an approved gateway mechanism.
- Expose only the intended web UI/API surface. Add authentication, rate limiting, and request validation to public endpoints.
- Do not bypass source access controls or scrape private/restricted data.

## Deployment and Teardown

- All infrastructure settings must be represented in `infra/`; do not make console-only changes without reflecting them in code.
- Run `scripts/verify-cloud-guardrails.sh` before deployment and record its output in the PR or demo checklist.
- For the hackathon demo, capture required Google Cloud proof first. After judging/demo requirements are satisfied, follow the teardown runbook to scale services to zero, disable schedulers, delete disposable datasets/artifacts, and remove unused resources.
- Never run destructive teardown commands without displaying the target project/environment and receiving explicit confirmation from the human developer.
```

---

## 3. Make the Rules Real in `infra/` and CI

A `CLAUDE.md` instruction can be ignored or misunderstood. Terraform/Pulumi configuration and CI validation are the enforcement layer.

### Required IaC guardrails

| Control | Enforce in infrastructure | Verify in CI/script |
|---|---|---|
| Scale to zero | `min_instances = 0` / equivalent Cloud Run configuration | Fail if a non-exempt service has minimum instances above zero. |
| Maximum capacity | Finite Cloud Run `max_instances`; bounded task dispatch/concurrency | Fail if max is missing or exceeds the project’s documented limit. |
| Minimal resources | CPU/memory variables with conservative environment defaults | Flag resource classes above approved demo threshold. |
| Authenticated endpoints | Cloud Run IAM, gateway/auth configuration, or a documented public exception | Fail if sensitive endpoint is unauthenticated. |
| Secrets | Secret Manager references; no literal secret values | Secret scan and IaC check. |
| Storage lifecycle | Lifecycle/retention rules per bucket | Fail if temp/raw buckets lack lifecycle policy. |
| Budget alerts | Billing budget resource/manual setup record | Verify alert configuration exists; document its project ID and recipients. |
| Teardown | Resource labels and environment separation | Script lists/deletes only resources with approved project/environment labels. |

### Example `.env.example`

```dotenv
# Non-secret defaults only. Never commit real API keys or credentials.
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
DEPLOY_ENV=demo

# Guardrails
CLOUD_RUN_MIN_INSTANCES=0
CLOUD_RUN_MAX_INSTANCES=2
CLOUD_RUN_CPU=1
CLOUD_RUN_MEMORY=512Mi
TASK_MAX_CONCURRENT_DISPATCHES=2
TASK_MAX_RETRY_ATTEMPTS=3

# Model policy
DEFAULT_GEMINI_MODEL=gemini-3.5-flash
ALLOW_PREMIUM_MODEL=false

# Retention in days; choose values appropriate to source/partner policy.
TEMP_ARTIFACT_RETENTION_DAYS=7
TRANSCRIPT_RETENTION_DAYS=30
```

### Example CI policy intent

```text
Fail the infrastructure validation job when:
- a Cloud Run service has no maximum instance cap;
- a demo/background service has a minimum instance count above zero;
- a service is public without an explicit documented exception;
- a bucket lacks a lifecycle policy;
- a service account has owner/editor or overly broad permissions;
- a secret-like value appears in tracked files;
- an environment lacks resource labels needed for teardown.
```

Do not blindly copy provider-specific resource syntax from an AI response. Have Claude Code inspect the exact Terraform/Pulumi provider version and existing project modules before editing `infra/`.

---

## 4. Add a Claude Code Skill for Deployments and Cost Reviews

Use a skill when you want Claude Code to follow a repeatable process such as “review this deployment plan” or “prepare a demo teardown.”

### Copy-paste `.claude/skills/gcp-ops-review/SKILL.md`

```md
---
name: gcp-ops-review
description: Review CivicTrace Google Cloud changes for cost, security, lifecycle, and demo-readiness guardrails.
---

# CivicTrace GCP Operations Review

Use this skill before deploying, changing infrastructure, starting a corpus backfill, exposing an endpoint, recording the hackathon demo, or tearing down demo resources.

## Procedure

1. Read `CLAUDE.md`, `.claude/rules/gcp-operations.md`, the affected `infra/` files, and the applicable runbook.
2. Summarize the planned resources, service identities, endpoints, storage buckets, expected model calls, and expected data retention.
3. Check scale-to-zero, finite maximum instances, minimal CPU/memory, bounded queue concurrency, retry limits, model selection, storage lifecycle, endpoint authentication, least-privilege service accounts, secret handling, and teardown labels.
4. Classify each issue as BLOCKER, REQUIRED_FIX, or RECOMMENDATION.
5. Do not deploy, change billing, expose endpoints, or run destructive teardown. Present an explicit plan and wait for human approval.

## Required Output

Return a markdown table with: Control, Current State, Risk, Required Change, Verification Command/Test, and Owner.

## Stop Conditions

Stop and request human direction if a change would expose a public endpoint, enable external publishing/outreach, increase a service cap, use a premium model, create an always-on resource, or delete resources.
```

---

## 5. Add a Narrow Infrastructure Reviewer Subagent

A reviewer subagent is useful for analysis, not for automatic deployment. Define it under `.claude/agents/` with read-only tools where practical.

### Copy-paste `.claude/agents/gcp-ops-reviewer.md`

```md
---
name: gcp-ops-reviewer
description: Reviews CivicTrace infrastructure changes for cost, security, lifecycle, and deployment guardrails. Does not deploy or alter cloud resources.
tools: Read, Glob, Grep
---

You are the CivicTrace GCP Operations Reviewer.

Review only repository files and supplied deployment plans. You do not run deployment commands, alter cloud resources, change billing, expose endpoints, or access credentials.

Evaluate each relevant change against:
- `CLAUDE.md`
- `.claude/rules/gcp-operations.md`
- `docs/runbooks/cost-control.md`
- `docs/runbooks/demo-teardown.md`

Flag these as BLOCKER unless an explicit approved exception exists:
1. A Cloud Run service without a finite maximum instance cap.
2. A demo/background service with minimum instances greater than zero.
3. An unauthenticated or unprotected sensitive endpoint.
4. Broad service-account roles, embedded secrets, or missing storage lifecycle rules.
5. A premium model used by default without benchmark/rationale.
6. An always-on database/vector cluster introduced without written approval and cost rationale.
7. A deployment plan with no rollback/teardown procedure.

Return: findings table, exact files/lines, risk explanation, required remediation, and verification step. Do not make changes.
```

---

## 6. Use `.claude/settings.json` for Tool Permissions, Not Policy Prose

Use project `settings.json` for the operational behavior Claude Code can enforce through its own configuration—permissions, hooks, and non-secret environment variables. Keep machine-specific or personal choices in `settings.local.json`, which should be ignored by Git. Claude Code’s documentation specifically separates project context from permissions/hooks/settings and local overrides. [1]

Do **not** put API keys or real service-account credentials in either settings file. Use Secret Manager for deployed services and untracked local environment configuration for development.

A good starting approach is to keep destructive commands requiring confirmation rather than trying to auto-allow every cloud command. Add project hooks only after testing them in a non-production project; a bad hook can block normal development.

---

## 7. Put the Operational Detail in Runbooks

Create four short, human-readable runbooks under `docs/runbooks/`:

| Runbook | Required contents |
|---|---|
| `deploy.md` | Prerequisites, environment selection, infrastructure plan review, deployment command, smoke checks, rollback, and required approval points. |
| `cost-control.md` | Budget name/thresholds, alert recipients, service caps, expected cost drivers, current corpus limits, pre-backfill checklist, and cost-status command. |
| `incident-and-recovery.md` | Source failure, queue backlog, failed extraction, duplicate event, secret exposure, and publication-gate incident procedure. |
| `demo-teardown.md` | Verify video proof captured; disable scheduler; drain/stop queues; scale services to zero; delete disposable artifacts/datasets; review billing/resource inventory; retain only required project evidence. |

### Copy-paste `docs/runbooks/demo-teardown.md` outline

```md
# Demo Teardown Runbook

## Preconditions

- Demo video and Google Cloud proof have been captured and safely backed up.
- The human project owner confirms teardown target: project ID, environment, region.
- No teammate or judge needs the live application during the teardown window.

## Procedure

1. Run `scripts/cost-status.sh` and save the output.
2. Disable Cloud Scheduler jobs and pause nonessential source watchers.
3. Confirm Cloud Tasks/Pub/Sub work is drained or intentionally discarded according to the environment policy.
4. Scale Cloud Run services to zero or delete explicitly disposable demo services through IaC.
5. Apply storage lifecycle cleanup or delete only environment-labeled temporary artifacts.
6. Delete disposable BigQuery/demo resources as defined in `infra/`.
7. Review active services, buckets, service accounts, and billing usage.
8. Record the teardown date, operator, resources retained, and resources deleted.

## Safety Rule

Never execute destructive commands without printing the target project, environment, and resource list and receiving explicit human confirmation.
```

---

## 8. What Not to Do

| Anti-pattern | Better approach |
|---|---|
| Paste every cloud tip into `CLAUDE.md`. | Keep it concise; link to rules and runbooks. |
| Rely on prompts to prevent an expensive deployment. | Enforce resource caps, lifecycle, and identity rules in IaC and CI. |
| Put secrets in Claude settings, `CLAUDE.md`, or the repository. | Use Secret Manager and ignored local development files. |
| Let a general coding agent deploy or delete freely. | Use a review skill/subagent, required confirmation, and versioned scripts. |
| Use one production project for development, demo, and experimentation. | Separate environments/projects where possible; at minimum label all resources by environment. |
| Auto-tear down immediately after recording. | Preserve the deployed proof until the submission is accepted and the owner confirms it is safe to turn off. |
| Assume budget alerts cap charges. | Pair alerts with resource caps, concurrency limits, quotas, and cost telemetry. |

## Recommended Next Action

Start with these three files only:

1. `CLAUDE.md` — short non-negotiable summary.
2. `.claude/rules/gcp-operations.md` — detailed instructions above.
3. `docs/runbooks/demo-teardown.md` — human-controlled cleanup process.

Then add `infra/` policy checks and the review skill before the first real deployment. This gives Claude Code the right context while ensuring the most important cost and security guarantees are enforced outside the model.

## Reference

[1]: https://code.claude.com/docs/en/claude-directory "Claude Code Docs — Explore the .claude directory"
