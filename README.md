# CivicTrace

> **CivicTrace turns public promises into living, evidence-linked case files—and wakes up when the public record changes.**

CivicTrace is an approval-gated public-evidence system for local accountability. The hackathon MVP follows one City of Milwaukee public commitment from an official record through later public evidence and produces a human-reviewable **Decision Delta** plus an inquiry-ready research packet. It does not publish claims, submit requests, or contact anyone autonomously.

## Start Here

1. Read [`CLAUDE.md`](CLAUDE.md) before asking Claude Code to change the project.
2. Read the [PRD](docs/product/PRD.md) for the product, scope, data model, and safety boundary.
3. Read the [multi-agent design](docs/architecture/multi-agent-design-and-prompts.md) before implementing agents.
4. Read the [Google stack decision](docs/architecture/google-agent-stack-decision.md) before choosing services or infrastructure.
5. Read the [Milwaukee go/no-go](docs/research/milwaukee-go-no-go.md) before writing source adapters.

## MVP Scope

| Build now | Build after the City loop works |
|---|---|
| Direct Milwaukee Legistar source adapter | MPS Board/meeting monitor extension |
| Selected Milwaukee CKAN structured-data adapter | Speech-to-Text batch media pipeline |
| Cloud Storage artifact vault | County source adapters |
| ADK evidence → entity → case → delta workflow | Parallel research-discovery feature |
| Firestore evidence/case/approval ledger | TinyFish fallback adapter, only if direct retrieval fails |
| Cloud Tasks/Pub/Sub async job workflow | CMS/email/records-request integrations |
| Evidence Studio and human-approved inquiry packet | Broad citywide monitoring |

## Architecture

![CivicTrace architecture](docs/architecture/civictrace-architecture.png)

![Promise Ledger flow](docs/architecture/promise-ledger-flow.png)

## Repository Guide

The full [Claude Code project pack guide](docs/claude-code-project-pack-guide.md) explains which artifacts were curated from the strategy work, why they are in the repository, and what implementation files remain to be created.

## Non-Negotiable Safety Rules

CivicTrace uses original public sources, preserves exact provenance, makes uncertainty explicit, excludes individual student data, avoids unsupported allegations/casual claims, and requires human approval for all external-facing action. See [`CLAUDE.md`](CLAUDE.md) and [privacy/evidence rules](.claude/rules/privacy-and-evidence.md).

## License

MIT — see [LICENSE](LICENSE). The public records under `backend/tests/fixtures/` are City of Milwaukee Legistar documents and remain public records; see `docs/sources/`.
