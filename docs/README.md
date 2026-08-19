# CivicTrace Documentation Index

| Area | Start here | Use it for |
|---|---|---|
| **Product** | [`product/PRD.md`](product/PRD.md) | Scope, user journeys, functional requirements, data model, safety boundaries, roadmap. |
| **Agent architecture** | [`architecture/multi-agent-design-and-prompts.md`](architecture/multi-agent-design-and-prompts.md) | ADK agents, system prompts, tool permissions, validation, approval, recovery, acceptance tests. |
| **Google stack** | [`architecture/google-agent-stack-decision.md`](architecture/google-agent-stack-decision.md) | ADK/Python/Vertex AI/Cloud Run/Firestore decision and service responsibilities. |
| **Visuals** | [`architecture/`](architecture/) | Editable Mermaid architecture/product-flow files plus rendered PNGs. |
| **External APIs** | [`integrations/api-stack-and-vendor-decision.md`](integrations/api-stack-and-vendor-decision.md) | Official source adapters, TinyFish/Parallel decision, secret/key inventory. |
| **Milwaukee and MPS** | [`research/`](research/) | Pilot choice, direct sources, meeting monitor, MPS privacy and procurement boundary. |
| **Hackathon** | [`hackathon/`](hackathon/) | Rules, prize strategy, demo plan, repo proof. |
| **Runbooks** | [`runbooks/`](runbooks/) | Cost/security implementation context, deployment, teardown. |
| **Source policy** | [`sources/`](sources/) | Domain allowlist and reviewed replay-corpus manifest. |
| **Testing** | [`evaluations/README.md`](evaluations/README.md) | Mandatory safety, grounding, idempotency, and approval test suites. |
| **Project pack guide** | [`claude-code-project-pack-guide.md`](claude-code-project-pack-guide.md) | What was copied from the conversation, why, and what remains to build. |

Use `CLAUDE.md` to decide what documentation must be read for a task. Do not load every document into every agent/task; retrieve the smallest relevant context set.
