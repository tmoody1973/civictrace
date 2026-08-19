# CivicTrace Google Agent Stack: Framework Decision and Implementation Map

## Executive Decision

**Build CivicTrace’s agent backend with Google ADK in Python, use Gemini 3.5 Flash through Vertex AI for production, deploy the API and workers on Cloud Run, and use Firestore as the durable case/agent-state ledger.**

Use **Google AI Studio** for rapid prompt and multimodal experiments during development, then move the production service identity and Gemini calls to **Vertex AI** before the recorded demo. Use **Antigravity as a development environment/productivity tool if it helps you build faster**, but do not make the Antigravity SDK the CivicTrace runtime. Do not add Genkit in the hackathon MVP unless the entire backend is already TypeScript and the team deliberately chooses Genkit instead of ADK.

> **One-sentence architecture:** ADK agents reason over bounded evidence; Cloud Tasks and Pub/Sub run the work asynchronously; Firestore preserves the accountable case state; Cloud Storage preserves raw public sources; BigQuery filters the large corpus; Cloud Run hosts the product; Vertex AI provides Gemini; humans approve every external-facing artifact.

---

## 1. Which Agent Framework Should You Use?

### Recommendation: **Google ADK, Python backend**

CivicTrace is a multi-agent, long-running, evidence-sensitive workflow. ADK is the best fit because it is specifically designed to grow from agents/tools into multi-agent systems, supports predictable graph-based workflows, has evaluation tooling, and can run on Cloud Run. ADK’s official materials emphasize deterministic code combined with adaptive reasoning and structured/graph-based orchestration—exactly the separation CivicTrace needs between the **orchestrator** and specialized evidence agents. [1] [2]

| Option | CivicTrace fit | Recommendation | Why |
|---|---|---|---|
| **ADK** | Excellent | **Use as the only agent framework in MVP.** | Native multi-agent composition, workflow/graph paths, tools, evaluation, Google Cloud deployment, and direct fit with the architecture/prize story. [1] [2] |
| **Antigravity SDK** | Potentially strong, but not the best product-runtime choice now | **Do not use as runtime MVP. Use Antigravity tooling only if helpful during development.** | Its harness offers subagents and lifecycle/safety hooks, but CivicTrace needs an explicitly durable, event-driven backend where you control queue, ledger, state, and approval boundaries. Adding it alongside ADK creates framework duplication. [3] |
| **Genkit** | Good framework, especially for TypeScript full-stack apps | **Do not combine with ADK in MVP.** | Genkit is excellent for AI flows, structured output, tool calling, RAG, and general app AI features, but ADK more directly fits the multi-agent/control-plane story. Use Genkit instead of ADK only if you deliberately make a TypeScript-only product and simplify the agent topology. [4] |
| **No framework; raw Gemini calls** | Inadequate | **Do not choose.** | It will look like model calls wired together, not a robust multi-agent system with evaluation, routing, tool boundaries, and lifecycle discipline. |

### Why Python for the agent service

Choose Python for the ADK backend because the CivicTrace evidence pipeline is naturally Python-friendly: PDF/OCR/table processing, data ingestion, Pydantic schemas, asynchronous workers, and public-data adapters are straightforward. Keep the browser UI in TypeScript/React if desired. The frontend calls CivicTrace’s own API; it never calls Gemini or ADK directly.

---

## 2. How to Use Each Google Product

| Product | Exact CivicTrace responsibility | Use it this way | Do not use it for |
|---|---|---|---|
| **Gemini API & Google AI Studio** | Prototype prompts, structured schemas, multimodal document/video experiments, and UX copy. | Test the Document Evidence, Media Evidence, Delta Investigator, and Brief Builder prompts with representative public artifacts. Keep test fixtures and expected schema outputs in Git. | Production secrets, production user data, or the authoritative durable case state. |
| **Vertex AI Gemini** | Production inference for all ADK agents. | Use Gemini 3.5 Flash by default for extraction, classification, entity-link proposals, delta comparison, and drafts. Authenticate through Cloud Run service identity; log model/version/request class. | A substitute for source storage, verification, or deterministic approval logic. |
| **ADK** | Agent definitions, typed inputs/outputs, tools, evaluation suites, and graph workflow. | Implement the eight specialized agents and their prompts from the CivicTrace multi-agent package. Keep the main workflow graph narrow and deterministic. | Queueing, storage, IAM policy, raw source archival, or direct external publishing. |
| **Cloud Run** | Public product/API surface and private worker endpoints. | Deploy `civictrace-api` for editor/UI API and `civictrace-worker` for Cloud Task jobs. Scale to zero, finite max instances, service-specific identities, authenticated internal invocation. | Holding durable workflow state in RAM or running unbounded polling loops. |
| **Firestore** | Durable operational state and audit ledger. | Store cases, commitments, evidence pointers, jobs, approvals, reviewer corrections, and immutable ledger events. Use document IDs/idempotency keys for safe retries. | High-volume raw public data, source binary files, or a generic vector database. |
| **Cloud Storage** | Immutable raw evidence vault. | Store downloaded public documents, raw JSON snapshots, permitted public media, timestamped transcript files, and generated packets. Keep canonical URL, hash, retrieval time, and lifecycle rule. | Ephemeral application sessions or untracked scratch output. |
| **Pub/Sub** | Source/event fan-out. | Publish `source.discovered`, `artifact.stored`, `transcript.completed`, `case.changed`, and `approval.granted` events. | Performing heavy work synchronously inside event delivery. |
| **Cloud Tasks** | Bounded, retried, idempotent work execution. | Dispatch extraction, transcription polling, entity resolution, case update, and packet rendering to `civictrace-worker`; set finite concurrency/retry limits. | An unbounded background-agent loop. |
| **Cloud Scheduler** | Periodic source checks. | Trigger direct City Legistar/CKAN/MPS adapters at controlled cadences. Disable for replay-only demo or after demo teardown. | Querying sources excessively or replacing a source’s push/webhook API when one exists. |
| **BigQuery** | Large structured corpus, historical backfill, prefiltering. | Land selected CKAN/Legistar-derived rows with source/date/entity partitioning. Query exact candidate rows before Gemini receives a small evidence packet. | Storing every UI state field or using LLMs to scan the entire dataset. |
| **Cloud Speech-to-Text V2** | Asynchronous public-meeting transcription. | Copy/retain permitted public audio in Cloud Storage, submit a batch operation, save operation ID/transcript/timestamps, then pass bounded segments to the Media Evidence Agent. | Named speaker identification based only on diarization labels. |
| **Secret Manager + IAM** | Secrets and least privilege. | Keep API keys in Secret Manager; give each Cloud Run service a minimal role; authenticate internal calls through IAM. | Browser-stored keys or shared project-owner credentials. |
| **Cloud Logging + Cloud Trace** | Operational and demo observability. | Record source event → task → agent version → validation → case change → approval chain. Show this trace during the demo. | Storing raw sensitive source material in logs. |
| **Firebase Auth / Identity Platform** | Optional editor/reviewer login. | Add when there are multiple reviewers; bind approval records to user ID and role. | Making a source artifact public by default. |
| **Vertex AI embeddings / BigQuery vector search** | Optional later retrieval support. | Add only after simple BigQuery/date/entity filtering is insufficient; embed parsed public chunks and retrieve a small evidence set. | An MVP requirement or excuse to introduce an always-on vector cluster. |

---

## 3. The Correct Division Between Google AI Studio and Vertex AI

### During build: Google AI Studio

Use Google AI Studio to move quickly on the **agent prompts**, test schemas, and test how Gemini handles a real Milwaukee agenda, scanned document, table, or MPS meeting transcript. Keep a small set of de-identified/public evaluation fixtures. The output of this stage is not the product—it is a versioned prompt/schema/evaluation suite you port to ADK.

### In the deployed product: Vertex AI

Use Vertex AI in Cloud Run for production inference. This removes browser-held keys, uses service identities and IAM, centralizes billing/observability, and makes the demo’s Google Cloud deployment clear. The same Gemini Flash model family remains the default, but every agent invocation is associated with an ADK workflow state, an immutable source bundle, an agent version, and a trace ID.

| Stage | Gemini access | Purpose | Data boundary |
|---|---|---|---|
| **Prompt laboratory** | Google AI Studio / Gemini API | Develop and evaluate prompts against public fixtures. | Public, curated test content only. |
| **Local application** | Gemini API or Vertex AI development project | Run ADK locally with fixture/replay corpus. | No production credentials or user-sensitive records. |
| **Demo/pilot deployment** | Vertex AI with Cloud Run service account | Serve live/replay jobs, agents, and Evidence Studio. | Approved public source artifacts plus authorized reviewer state. |

---

## 4. ADK Architecture for CivicTrace

### 4.1 Do not make one free-form “super agent”

Use ADK to define specialized agents with restricted tools and schemas. The application control plane—not a model—controls job routing, persistence, retries, idempotency, and approvals.

| ADK agent | Gemini role | Input | Output | Tool permissions |
|---|---|---|---|---|
| **Document Evidence Agent** | Multimodal structured extraction | One document/artifact plus page/table map. | Cited evidence, commitments, votes, dates, limits. | Read artifact only. |
| **Media Evidence Agent** | Transcript/media fact extraction | Timestamped transcript, diarization labels, public meeting context. | Timestamped facts/segments; no unsupported named attribution. | Read transcript/media metadata only. |
| **Entity Resolution Agent** | Conservative candidate matching | Valid evidence + bounded candidate list. | Confirmed/candidate/rejected public-entity links. | Read candidate index/corrections only. |
| **Case Linker** | Evidence-to-case relevance reasoning | Valid evidence, links, active case summaries. | Link/no-link/candidate case proposal. | Read case summaries only. |
| **Delta Investigator** | Original-versus-later record comparison | Frozen original commitment + later evidence. | Grounded Decision Delta or no-delta. | Read case bundle only. |
| **Quality & Safety Reviewer** | Policy and evidence review | Proposed output + source map. | Approve/reject/revise with precise issue. | Read only. |
| **Inquiry Planner** | Narrow next-question drafting | Approved evidence gap. | Human-review inquiry outline. | Read templates/case only. |
| **Brief Builder** | Neutral draft composition | Approved meeting/case facts. | Five-section review-required brief. | Read only. |

### 4.2 ADK workflow shape

Use a graph/workflow style rather than letting agents self-delegate indefinitely:

```text
Direct source adapter
  → SourceEvent + raw artifact
  → Cloud Task: document/media extraction
  → ADK Evidence Agent
  → deterministic schema/provenance validator
  → ADK Entity + Case Linker
  → deterministic ledger update
  → ADK Delta Investigator
  → ADK Quality Reviewer
  → Firestore staged case
  → human approval
  → ADK Inquiry Planner / Brief Builder
  → deterministic Artifact Worker
```

ADK’s graph-oriented orchestration and support for multi-agent systems is a good fit for this explicit path. [1] [2]

---

## 5. Firestore Data Model

Firestore is the system’s **operational ledger and agent memory**, but not a dumping ground for whole PDFs/media.

```text
/users/{userId}
/source_configs/{sourceId}
/source_events/{eventId}
/artifacts/{artifactId}                # metadata + GCS pointer + hash
/evidence/{evidenceId}                 # precise anchor + extracted text + status
/entities/{entityId}
/cases/{caseId}
/cases/{caseId}/ledger_events/{eventId}
/cases/{caseId}/evidence_refs/{evidenceId}
/jobs/{jobId}
/approvals/{approvalId}
/corrections/{correctionId}
/evaluations/{runId}
```

| Collection | What it records | Why it matters to judges |
|---|---|---|
| `source_events` | Source ID, fingerprint, external ID, discovery time, status. | Shows event-driven autonomy and idempotency. |
| `artifacts` | Immutable GCS pointer, content hash, canonical URL, retrieval time. | Shows provenance and replayability. |
| `evidence` | Anchor, excerpt, supported/candidate/conflicting/unknown state. | Shows that agent output is inspectable. |
| `cases` + `ledger_events` | Current Promise Ledger view and immutable update history. | Shows durable long-term memory. |
| `jobs` | Task state, retry count, input/output references, trace ID. | Shows asynchronous fault tolerance. |
| `approvals` | Case-bound artifact/action approval, reviewer, expiry. | Shows human control over side effects. |
| `corrections` | Reviewer entity/source corrections. | Shows continuous learning through governed feedback. |

---

## 6. Cloud Run Deployment Layout

| Service | Exposure | Responsibilities | Key configuration |
|---|---|---|---|
| `civictrace-api` | Browser-facing, authenticated | Evidence Studio API, editor inbox, review/correction/approval endpoints. | `min=0`, finite `max`, Firebase/Identity auth, no Gemini key in browser. |
| `civictrace-worker` | Internal only; IAM-authenticated Cloud Tasks target | Adapter retrieval, artifact preservation, ADK runs, validation, graph updates, packet rendering. | `min=0`, finite `max`, queue concurrency cap, least-privilege service account. |
| `civictrace-web` | Optional public/authenticated UI | React/Next.js static or server-rendered user interface. | Keep separate from worker privilege. |

Do not deploy an always-on “agent runtime” process. Cloud Scheduler triggers small adapter checks, Pub/Sub emits events, and Cloud Tasks causes scale-to-zero workers to start only when work exists.

---

## 7. Build Sequence: First Ten Moves

| Order | Build it | Proves |
|---:|---|---|
| 1 | Create Google Cloud project, budgets, labels, service accounts, and a minimal Cloud Run hello-world. | Deployment readiness and spend control. |
| 2 | Use AI Studio to prototype one Document Evidence Agent schema against a real public Milwaukee artifact. | Gemini can generate source-cited structured data. |
| 3 | Create the ADK Python service with a single agent and evaluation fixture. | The framework choice is real, not slideware. |
| 4 | Add Cloud Storage artifact vault and Firestore evidence/case documents. | Provenance and durable state. |
| 5 | Build direct Milwaukee Legistar adapter plus content fingerprint. | Real source watcher. |
| 6 | Add Pub/Sub + Cloud Tasks + internal Cloud Run worker. | Asynchronous heavy lifting. |
| 7 | Add Entity/Case/Delta agents and deterministic grounding checks. | Persistent reasoning across time. |
| 8 | Build Decision Delta Studio in the web UI. | Multimodal inspectability. |
| 9 | Add approval-token and packet-renderer services. | Safe, complete Taskmaster workflow. |
| 10 | Add Speech-to-Text and MPS adapter only after City loop passes replay, duplicate-event, and missing-source tests. | Multimodal expansion without scope risk. |

---

## 8. What to Tell the Judges

> “CivicTrace uses ADK for specialized, schema-constrained Gemini agents; Cloud Tasks and Pub/Sub for asynchronous execution; Firestore as an evidence and approval ledger; Cloud Storage for immutable public-source artifacts; BigQuery to narrow a large civic corpus before model reasoning; and Cloud Run to deploy secure, scale-to-zero API and worker services. The model never owns state or publication: code validates every agent output, and a human approves every external-facing action.”

That is a much stronger explanation than claiming to use every Google product. It connects each service to an actual reliability, cost, safety, or user-value requirement.

---

## References

[1]: https://adk.dev/ "Google ADK — Build production agents, not prototypes"

[2]: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk "Google Cloud — Agent Development Kit"

[3]: https://antigravity.google/docs/home "Google Antigravity Documentation"

[4]: https://genkit.dev/docs/js/overview/ "Genkit Documentation — Overview"
