# CivicTrace Prize-Competition Blueprint

**Submission track:** The Taskmaster  
**Prize posture:** Build one system that is visibly credible for Taskmaster, Best Architectural Design, and Best Multimodal UX.  
**Core claim:** *CivicTrace is not a public-records chatbot. It is a durable civic evidence engine that watches a territory, does the back-office work of an investigative beat, and returns a source-grounded inquiry when the public record changes.*

> **The winning test:** A judge should be able to point to one live run and say, “This agent handled a corpus, remembered its work, discovered a meaningful change, survived a failure, and showed me the original evidence in the medium where it matters.”

## 1. Turn the Broad Theme into a Competitive Advantage

The hackathon rewards systems that run in the background, carry out complex asynchronous workflows, and manipulate difficult representations rather than merely converse. The published score allocates 40% to innovation and operational utility, 30% to architecture, and 30% to demo/production readiness; it specifically asks Taskmaster entrants to complete a multi-step background workflow and asks architecture judges to evaluate modularity, state, tool isolation, and failure tolerance.[1]

CivicTrace should therefore build **one evidence-to-inquiry loop** so complete that it proves all of those traits simultaneously.

| Requirement | CivicTrace proof | The exact line to use in the pitch |
|---|---|---|
| **Heavy lifting of massive datasets** | A historical backfill and continual delta ingest turn thousands of City records, agenda items, attachments, data rows, and media segments into a queryable, source-provenance graph. | “CivicTrace does not answer questions over a folder. It continuously compiles a civic memory from years of records.” |
| **Asynchronous autonomy** | A watcher triggers a durable job graph; source discovery, extraction, entity linking, graph updates, delta detection, and packet generation happen in the background. | “The newsroom does not keep prompting it. CivicTrace wakes up when the public record changes.” |
| **Complete Taskmaster workflow** | It moves from a source change to a human-approved inquiry packet containing citations, video timestamps, missing-record logic, and draft questions. | “The outcome is an investigation-ready case, not a generated paragraph.” |
| **Architectural Design** | Event sourcing, typed state, immutable raw artifacts, idempotent workers, dead-letter recovery, scoped action tokens, source provenance, and evaluation tests are visible in the UI and code. | “The agent can reason, but only deterministic workers are allowed to act.” |
| **Multimodal UX** | The decision delta can be interrogated through a PDF/table, meeting audio/video clip, map, structured records, and timeline—each with a source location and correction path. | “A user can see, hear, locate, and challenge every conclusion.” |

## 2. Build Corpus-Scale, Not a One-PDF Demo

“Massive datasets” does not require pretending you have the entire government data estate. It requires an architecture that treats source volume, replay, and incremental updates as first-class concerns. Define a reproducible Milwaukee **corpus manifest** that can backfill several years of City legislative records plus selected City open-data datasets. The live demo may focus on a single project, but the interface must show that the same pipeline has processed a territory-wide corpus.

### The Corpus Contract

| Layer | Design | Why it competes |
|---|---|---|
| **Raw truth** | Store every retrieved PDF, HTML snapshot, CSV/JSON response, video/audio metadata, and source URL in Cloud Storage with a content hash and retrieval timestamp. | A model output can always be traced to the immutable original. |
| **Tabular scale** | Load public tabular records to BigQuery, partitioned by source and date. Treat one event/file/data-row delta as a small, independently rerunnable unit. | It separates corpus-scale retrieval/filtering from LLM reasoning. |
| **Semantic evidence** | Chunk artifacts with page/table/timestamp coordinates. Store embeddings and case links in a case-scoped vector index or retrieval layer. | The model retrieves only evidence relevant to a claim; it does not carry the city in its context window. |
| **Operational state** | Firestore stores case state, job status, source fingerprints, user feedback, approval tokens, and an append-only evidence/action ledger. | The agent resumes correctly after latency, refreshes, or failures. |
| **Incremental work** | A source watcher fingerprints new/changed items; unchanged records are skipped, while a changed event only fans out to its dependent work. | This is genuine asynchronous data engineering, not an expensive repeated prompt. |

### What to Show in the Product UI

Include a small **Civic Memory Console** accessible from the case screen. It is not a dashboard for its own sake; it proves the system’s capacity.

| UI element | Live value to the user | Value to judges |
|---|---|---|
| `12,xxx sources indexed · 3,xxx documents parsed · 100% resumable` | A newsroom knows whether its territory is current. | The workload is visibly larger than a one-off chat request. Use the actual counts produced by your run. |
| Backfill progress by source/date partition | An editor can understand coverage gaps. | Shows parallel, durable background processing. |
| “New source discovered” event and dependent job graph | A person sees why a case changed. | Shows event-driven orchestration, not magic. |
| Source fingerprint and raw-artifact link | A user can inspect original evidence. | Demonstrates provenance and reproducibility. |
| Replay button restricted to editors | A case can be recomputed after a correction. | Demonstrates controlled recovery and observability. |

## 3. The Architecture That Can Win Best Architectural Design

![CivicTrace competition architecture](assets/civictrace_competition_architecture.png)

### The Design Principle: Reasoning Is Not Authority

CivicTrace earns credibility by separating **agent reasoning** from **irreversible action**. Gemini and ADK agents can extract, compare, propose, and plan; they cannot publish a claim, submit a records request, contact a source, or overwrite the evidence state. An approval-gated deterministic worker does those limited actions only after a human issues a case-bound token.

| Component | Google technology | Responsibility | Architectural proof |
|---|---|---|---|
| **Source Watcher** | Cloud Run + Cloud Scheduler | Polls the City Legistar and CKAN adapters; emits a source event only when a fingerprint changes. | Update detection is cheap, repeatable, and independent of the UI. |
| **Durable event fabric** | Pub/Sub + Cloud Tasks | Publishes source events, fans out idempotent jobs, rate-limits third-party APIs, and retries transient failures. | The task survives browser closure and handles at-least-once delivery safely. |
| **Immutable source vault** | Cloud Storage | Persists the raw original with content hash, source URL, and retrieval time. | Every derived item has an inspectable primary source. |
| **Multimodal extractor** | Gemini 3.5 Flash via Vertex AI + Google ADK | Reads PDFs/tables, transcribes or reasons over meeting media, extracts commitments/entities/claims with structured output. | Demonstrates Gemini on the actual hard representation, not text pasted into chat. |
| **Evidence graph** | Firestore + typed schemas | Stores `Commitment`, `Decision`, `Project`, `Vendor`, `Evidence`, `Unknown`, `Conflict`, and `Inquiry` nodes plus provenance edges. | The agent remembers state for months and distinguishes fact, conflict, and absence. |
| **Corpus analytics** | BigQuery | Holds high-volume structured records and executes prefiltered joins/aggregations before the model sees a narrow case context. | The system handles data scale rationally and avoids using an LLM as a database. |
| **Delta investigator** | ADK worker | Compares new evidence against a case’s commitments and prior state; creates a `DecisionDelta` only when it can cite both sides. | Demonstrates scoped, grounded autonomous reasoning. |
| **Bounded action worker** | Cloud Run / Cloud Tasks | Renders an inquiry packet and, only after approval, creates a draft question or records-request outline. | Demonstrates action without unsafe autonomous outreach. |
| **Observability and evaluation** | Cloud Logging, Cloud Trace, and repository test suite | Exposes job lineage, extraction failures, retries, grounding tests, and idempotency results. | Gives judges proof of production thinking. |

### Three Demonstrations That Must Be Live

**First: idempotency.** Trigger the same source-change event twice. The UI should show two delivery attempts but exactly one evidence object and one terminal job result. This takes 10 seconds and is more impressive than ten architectural buzzwords.

**Second: missingness.** Feed a meeting record whose attachment is absent or inaccessible. CivicTrace must create a visible `NOT_PUBLISHED` or `REQUEST_NEEDED` evidence state and propose a limited next step. It must not invent a conclusion.

**Third: recovery.** Stop or fail a worker during extraction, then show it resume from the durable job state rather than restarting the entire corpus. Capture the trace/log and job status in the video.

## 4. Build a Multimodal Experience That Cannot Be Replaced by Chat

The product’s screen should feel like an **evidence studio**, not a government dashboard and not a chatbot. The question it answers is: *“Can I personally verify why this changed?”*

### The Signature Interface: The Decision Delta Studio

A single case screen has five synchronized surfaces. Clicking any element keeps all other surfaces aligned to the same source moment.

| Surface | Media | User action | Why it is essential |
|---|---|---|---|
| **Promise card** | Agenda PDF / ordinance page / table cell | Open the exact clause, table, or vote connected to a commitment. | Public commitments often live in dense documents, not data rows. |
| **Hearing clip** | Video/audio, transcript, speaker/timecode | Play the 20–40 second relevant segment while viewing the source text. | Tone, qualification, and context can change the meaning of a statement. |
| **Place canvas** | Map, parcel/address, project geography, nearby service conditions | See where a commitment is supposed to materialize and toggle relevant public records. | Location connects policy language to lived public reality. |
| **Evidence timeline** | Chronological source cards across documents, meetings, datasets, and service records | Scrub from promise → later record → unresolved gap. | Time is the central representation of accountability. |
| **Graph and challenge mode** | Source-backed entity graph | Click “What would change this conclusion?” or correct a bad entity/source link. | Feedback makes the system adaptive and visibly honest about uncertainty. |

### The Multimodal Moment in the Demo

Do not demo a chat prompt. An editor opens a Decision Delta. The system highlights a commitment clause in a meeting packet, jumps to a precise hearing clip, shows the project on the map, and connects it to a later data record. The editor notices that a link is wrong and selects **“Not the same project.”** CivicTrace preserves that feedback as a disambiguation rule, recalculates the case, and explains what changed.

This wins the UX argument because input and output are both intrinsically multimodal. No text-only experience could provide the same evidence trail or correction capability.

## 5. The Four-Minute Proof Plan

The video must be a story of completed work. The official rules only evaluate the first four minutes and require clear Google Cloud deployment proof.[1]

| Time | Show | Judge takeaway |
|---:|---|---|
| **0:00–0:20** | A single sentence: “Local decisions outlive meetings, but the evidence trail usually dies there.” Show the empty case and the source corpus counter. | A consequential and specific problem. |
| **0:20–0:45** | A new Milwaukee City source event enters the watcher; the job graph fans out without user prompting. | Autonomous Taskmaster trigger. |
| **0:45–1:20** | Background workers fetch the raw artifact, parse a PDF/table, align a meeting clip, and update the graph. Use real job-status changes. | Multimodal, asynchronous heavy lifting. |
| **1:20–2:05** | Open the Decision Delta Studio: promise clause, hearing clip, map, timeline, and later record; show every claim’s source anchor. | Essential multimodal UX plus grounded output. |
| **2:05–2:35** | Agent proposes the precise missing record/question. An editor approves; the packet worker completes the inquiry artifact. | Complete workflow with human control. |
| **2:35–3:05** | Replay a duplicate event or show a deliberate failed attachment. The ledger remains correct; failure becomes `REQUEST_NEEDED`. | Best Architectural Design proof. |
| **3:05–3:30** | Show Cloud Run, Pub/Sub/Tasks, Firestore/BigQuery, Cloud Logging trace, and the architecture diagram. | Genuine Google Cloud deployment, not a local mock. |
| **3:30–4:00** | Return to the finished inquiry packet: “CivicTrace did not publish a claim. It made the next verifiable question impossible to miss.” | Memorable product boundary and public-interest value. |

## 6. Repository and Submission Proof Package

| Asset | Required content | Why it matters |
|---|---|---|
| **README** | One-command local replay; Cloud Run deployment; corpus manifest; environment variables; known scope limits; cost controls. | Meets reproducibility expectations. |
| **Architecture diagram** | The rendered diagram above plus Mermaid source. | Shows boundaries, state, trust, and failure handling. |
| **Architecture decision records** | Why Firestore vs. BigQuery; why agents cannot side-effect directly; idempotency strategy; source-provenance model. | Converts engineering choices into judge-readable evidence. |
| **Typed schema** | JSON/Pydantic schema for `Evidence`, `Claim`, `Commitment`, `DecisionDelta`, `Job`, and `Approval`. | Makes state and agent contracts concrete. |
| **Evaluation suite** | Grounding: every delta needs two source anchors; safety: no action without approval; idempotency: duplicate delivery creates no duplicate evidence. | Makes quality measurable. |
| **Corpus manifest** | URLs/source IDs, retrieval timestamps, hashes, license/terms notes, and a replay order. | Proves that scale is repeatable and sources are legitimate. |
| **Deployment proof** | Cloud Run URL, console screenshots, and logs/trace shown in video. | Satisfies the rules’ explicit deployment expectation. |

## 7. The Non-Negotiable Execution Checklist

| Priority | Requirement | Owner definition of done |
|---:|---|---|
| **P0** | One event watcher, one durable job queue, one raw source vault, and one Firestore ledger. | A real City source event creates a resumable case without UI intervention. |
| **P0** | One complete Promise → Project → Later Record → Inquiry loop. | The final inquiry packet is source-cited and human approved. |
| **P0** | Decision Delta Studio with PDF/table + meeting clip + map + timeline. | A user can navigate all four media without returning to a chat window. |
| **P0** | Grounding, duplicate-event, and missing-file tests. | Tests are visible and all pass in the demo repository. |
| **P1** | BigQuery backfill and source-count console. | The corpus visibly exceeds the single-case demo and runs in partitions. |
| **P1** | Cloud Trace and dead-letter/recovery view. | One controlled failure and recovery are captured in the demo. |
| **P1** | Persistent editor corrections/preferences. | A correction changes future entity matching or alert triage. |
| **P2** | County source adapter and financial-source automation. | Include only after the City loop is bulletproof. |

## 8. Do Not Lose the Prize by Overbuilding

Avoid an all-city crawler, a predictive “corruption score,” autonomous outreach, or a generic news/article generator. Those features make the project harder to trust and easier to dismiss.

The winning version has a narrower but more defensible ambition: **CivicTrace keeps one class of Milwaukee public promise alive across the documents, video, data, and time that normally bury it.** That is a real product, a hard agentic system, and a demo judges can verify.

## Reference

[1]: https://allthingsagentichackathon.devpost.com/rules "All Things Agentic Hackathon — official requirements, judging, submission, and prizes"
