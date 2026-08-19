# CivicTrace
## Comprehensive Product Requirements Document and Project Proposal

| Document attribute | Detail |
|---|---|
| **Product** | CivicTrace — a persistent public-evidence and accountability platform |
| **Pilot territory** | City of Milwaukee, Wisconsin |
| **Expansion territory** | Milwaukee Public Schools (MPS), followed by Milwaukee County where a case crosses jurisdictions |
| **Primary user** | Local reporters, editors, civic-newsroom researchers, public-interest nonprofits, and trained community documenters |
| **Primary submission category** | All Things Agentic Hackathon — **The Taskmaster** |
| **Secondary prize posture** | Best Architectural Design and Best Multimodal UX |
| **Primary technology commitment** | Gemini 3.5 Flash or newer, Google ADK, and Google Cloud services |
| **Document status** | Proposed build specification and hackathon project proposal |

---

## 1. Executive Summary

**CivicTrace is a public-interest accountability engine that gives local newsrooms and civic watchdogs a persistent, source-grounded memory of public promises.** It watches public meetings, agendas, documents, data feeds, and media; turns them into a durable evidence graph; detects when a later record changes an open commitment; and completes the background work required to create a human-reviewable inquiry case.

The product is deliberately **not** an article generator, meeting-note app, generic public-records search engine, or automated misconduct detector. Its output is a **Decision Delta**: a source-linked, time-aware account of what a public body committed to, what later evidence establishes or fails to establish, what remains unknown, and the exact next question or record needed to resolve the gap. An editor or other authorized reviewer must approve any external outreach, public-records request, or publication.

The pilot focuses on the **Milwaukee Promise Ledger**. The system follows a geographically bounded City Council or committee commitment—such as a development agreement, tax-increment-financing decision, capital project, or infrastructure action—from the original vote through public project/location records, observable money or execution signals, later service/condition evidence, and a human-approved inquiry artifact. Milwaukee offers a credible, manageable public-source foundation: a City CKAN data portal, public Legistar records, public spending surfaces, and a user-authentic local story. [6] [7]

CivicTrace then expands through a separate **Milwaukee Public Schools (MPS) adapter**. The MPS extension follows public Board commitments through public improvement plans, budget/contract/facility records, and publicly reported aggregate outcomes. It operates only on public institutional material and never ingests or infers student-level personal information. [10] [11]

> **Product promise:** “CivicTrace turns a public promise into a living, evidence-linked case file—and wakes up when the record changes.”

---

## 2. The Problem

### 2.1 The public-accountability capacity collapse

The core problem is not that public records do not exist. The problem is that public records are fragmented across agendas, minutes, scanned PDFs, meeting recordings, public notices, budgets, procurement systems, property data, service requests, and other sources that evolve over months or years. A meaningful local decision may be discussed in one meeting, approved in another, funded through a later process, implemented through a separate department, and only become visible in a neighborhood through conditions or service records much later.

Local newsrooms and civic organizations rarely have the staffing capacity to maintain that chain of evidence. Northwestern Medill reported that more than 3,200 U.S. print newspapers had disappeared since 2005, and that closures were continuing at more than two per week in its 2024 report. [4] Research examining newspaper closures found that municipal borrowing costs rose and government payrolls expanded afterward, outcomes consistent with the loss of local monitoring and accountability. [5] CivicTrace is designed to restore a narrow but essential institutional capability: **persistent, verifiable public oversight.**

### 2.2 Why existing tools do not solve the complete loop

Existing civic-information products perform valuable but incomplete functions. Agenda Watch / Big Local News collects and makes public-meeting documents searchable. Documenters mobilizes trained residents to monitor public meetings. MuckRock manages public-records-request workflows. Council Data Project makes legislative records and transcripts searchable. Government-side systems such as Granicus and CivicPlus help agencies manage agendas, meetings, and document publication. [9]

CivicTrace is differentiated by the workflow it completes after a document is discovered. It connects a public decision to a commitment, an entity, a place, later execution evidence, and an explicitly defined unknown. It then plans a bounded next inquiry and prepares a human-approved research artifact. In short:

> **Search tells a reporter which documents mention a topic. CivicTrace maintains the evidence chain that explains what changed and what must be asked next.**

### 2.3 The user’s actual job to be done

A local reporter or civic researcher needs to answer questions such as: “What did the Council promise about this project?” “Which later record confirms or changes that promise?” “What source document is missing?” “Which meeting should I monitor next?” and “Can I trust every fact in the brief I am about to publish?”

Today, answering those questions requires manually collecting records, watching video, comparing dates, joining names and locations, maintaining personal notes, and repeatedly rediscovering old context. CivicTrace takes on the repeated evidence work while preserving human editorial judgment.

---

## 3. Product Vision, Strategic Positioning, and Principles

### 3.1 Product vision

CivicTrace will become a reusable public-source accountability layer for cities, school districts, regional newsrooms, nonprofit investigations desks, university reporting labs, and community-information networks. Each territory uses the same core model—source adapters, immutable evidence, typed case state, persistent graph, delta detection, and approval-gated actions—while adding local source adapters and domain schemas.

The initial vision is intentionally more ambitious than a meeting monitor but narrower than a generalized “AI for government.” CivicTrace does not attempt to understand every public policy issue or determine whether any institution is performing well. It gives people a reliable, inspectable system for following selected commitments across public evidence over time.

### 3.2 Strategic position

| Positioning statement | Meaning in practice |
|---|---|
| **Not a chatbot** | The primary trigger is a source change, not a user prompt. The primary output is a case artifact, not generated conversation. |
| **Not a surveillance system** | CivicTrace monitors institutions and public records, not private individuals or students. It does not profile, predict, or infer sensitive personal characteristics. |
| **Not an allegation engine** | It records supported facts, conflicts, unknowns, and cited questions. It does not label behavior as misconduct or corruption. |
| **Not a government publishing platform** | It can ingest public records and prepare briefs, but an independent reviewer controls any public communication. |
| **An accountability operating system** | It creates durable case memory, tracks what evidence is expected next, and reduces the cost of maintaining public attention. |

### 3.3 Product principles

1. **Evidence before prose.** Every conclusion must be grounded in a source ID and a precise location: document page, table cell, timestamp, dataset row, or source URL.
2. **Reasoning is not authority.** Models may extract, compare, suggest, and plan; deterministic, scoped workers may act only through an approval gate.
3. **Unknown is a valid outcome.** Missing, delayed, contradictory, or inaccessible records must remain visible as uncertainty states rather than being smoothed into a plausible answer.
4. **Multimodality must be necessary.** Video/audio, PDFs, maps, structured records, and time are not decorative inputs; they are the evidence formats required to verify a public claim.
5. **Human judgment remains indispensable.** Users may correct entity links, source associations, and relevance signals; editors approve outreach and publication.
6. **The product should improve civic capacity, not replace civic labor.** CivicTrace amplifies reporters, documenters, community partners, and public-information professionals.

---

## 4. Hackathon Thesis and Prize Strategy

The All Things Agentic Hackathon requires Gemini 3.5 or newer, a Google agent framework such as ADK, and at least one Google Cloud infrastructure service. It expects next-generation autonomous agents that operate beyond ordinary chat loops, run in the background, handle large or complex data, and perform meaningful workflows. [1] The recommended category is **The Taskmaster**, whose emphasis is a complete workflow that performs multi-step work rather than merely writing text. [2]

The rules allocate 40% of the evaluation to Innovation & Operational Utility, 30% to Architectural Discipline & Tech Stack, and 30% to Demo & Production Readiness. The specialty awards recognize top-scoring projects in architecture and multimodal UX, but the rules state that each project is eligible for up to one prize. [3]

| Competition target | CivicTrace strategy |
|---|---|
| **The Taskmaster** | A source watcher autonomously executes the complete source-change → evidence → Decision Delta → inquiry-packet workflow. |
| **Massive data / complex workflow theme** | A resumable historical corpus backfill plus incremental updates process public datasets, documents, and media through durable queues and typed state. |
| **Best Architectural Design** | Prove event sourcing, idempotency, immutable artifacts, tool isolation, approval gates, failure states, retries, observability, and reproducible tests. |
| **Best Multimodal UX** | Make the Decision Delta Studio synchronize document clauses, tables, transcript/video clips, maps, timelines, and graph relationships so users can inspect and correct every conclusion. |
| **Demo readiness** | Show a real public-source replay, live Google Cloud deployment, architecture diagram, trace/log view, resilience behavior, and completed inquiry artifact in four minutes. |

---

## 5. Target Users and Stakeholders

| Persona | Context | Primary need | CivicTrace value |
|---|---|---|---|
| **Local reporter** | Covers multiple institutions with limited time and inconsistent public records. | Find consequential changes without re-reading every agenda or losing historical context. | Alerts, source-grounded cases, evidence clips, and a ready-to-review inquiry packet. |
| **Editor / investigations lead** | Must protect accuracy, manage limited resources, and approve publication. | Assess whether a lead is verified, material, and worth assigning. | Decision Delta with provenance, uncertainty, and approval-controlled next action. |
| **Civic-newsroom researcher / documenter** | Performs records collection and meeting observation for a community audience. | Turn raw observation into durable, connected public knowledge. | Structured meeting brief, promise updates, and source-backed watch list. |
| **Public-interest nonprofit / advocacy researcher** | Tracks a mission-relevant policy or project over time. | Monitor commitments without confusing advocacy claims with public facts. | A transparent case ledger and bounded research workflow. |
| **Community reader** | Wants to understand what changed in a specific neighborhood, school, or public project. | View a credible, plain-language explanation with original evidence available. | Human-approved brief with source links, map, timeline, and uncertainty labeling. |
| **MPS transparency stakeholder** | Parent group, education reporter, district-facing transparency team, or education nonprofit. | Follow public Board commitments and aggregate outcomes without exposing student data. | MPS Promise Ledger using only public institutional evidence. |

---

## 6. Scope and Release Strategy

### 6.1 Release sequence

| Release | Objective | Included | Explicitly excluded |
|---|---|---|---|
| **Hackathon MVP — Milwaukee City Promise Ledger** | Prove a complete, reliable source-to-inquiry loop for one real historical case. | City Legistar adapter; selected CKAN sources; raw artifact vault; source-provenance graph; Decision Delta Studio; human-approved inquiry packet; Cloud deployment; failure and duplicate-event tests. | Citywide live investigation of every issue; autonomous outreach; every City/County system; allegation scoring. |
| **MPS demonstration extension** | Demonstrate a second institutional adapter and public education-accountability use case. | MPS agenda/meeting-media adapter; batch transcription; public plan/report-card link; staged MPS brief. | Student-level data; attendance/discipline prediction; dynamic procurement scraping. |
| **Pilot product** | Support one newsroom or civic partner across a defined beat. | Scheduled source monitoring; editor inbox; reusable topic/entity watch lists; source adapter configuration; publish-to-draft workflow. | Unsupervised publication; large-scale multi-tenant marketplace. |
| **Platform expansion** | Add jurisdictions and domain packs. | County adapters; procurement/export connectors; city/school source templates; fine-tuned civic extraction evaluation; partner integrations. | One generalized model expected to reason perfectly across all jurisdictions without source adaptation. |

### 6.2 MVP definition of done

The MVP is complete only when it can replay a documented public Milwaukee source bundle and produce one source-cited Decision Delta and inquiry packet without manual data manipulation during the run. The system must preserve the raw artifacts, survive a duplicate event without duplicated evidence, handle a missing attachment as an explicit uncertainty state, and show Cloud deployment proof.

---

## 7. Success Metrics

### 7.1 Product-quality metrics

| Metric | Definition | MVP target |
|---|---|---|
| **Source grounding coverage** | Share of Decision Delta statements with at least one precise source anchor; material comparisons require two anchors. | 100% for displayed claims; 100% of material deltas cite both the original and later evidence. |
| **Duplicate-event safety** | Duplicate source-event deliveries that produce no duplicate evidence or external artifact. | 100% in automated test fixture. |
| **Uncertainty integrity** | Missing/conflicting records correctly represented as explicit state rather than unsupported assertion. | 100% in test fixture set. |
| **Case refresh latency** | Time from detected source change to staged case update under normal test conditions. | Measured and displayed; optimized after correctness, not before. |
| **Editor correction persistence** | A confirmed source/entity correction changes future retrieval/matching behavior for the case. | Demonstrated in one live case. |
| **Inquiry completion** | A user can approve a staged inquiry and receive a complete source packet. | One end-to-end live run. |

### 7.2 Competition-proof metrics

The demo should display actual run counts rather than invented scale claims: source artifacts indexed, pages/media minutes processed, entity links created, jobs completed, retries, and unresolved evidence states. The architecture is designed to process a partitioned historical corpus and incremental updates; the final number displayed must be whatever the real replay corpus produces.

---

## 8. Non-Goals

CivicTrace will not infer causality between a public policy and a social outcome, publish allegations, score public officials or institutions for integrity, recommend interventions for individual students, collect private resident or student data, send messages or file requests without approval, or promise universal coverage of an entire municipality. These boundaries are product strengths: they make the system inspectable, safer, and more credible to reporters and judges.


---

## 9. Core User Journeys

### 9.1 Journey A: Milwaukee City source change becomes an inquiry case

**Trigger:** A City Legistar adapter detects a new, updated, or finalized meeting event, agenda item, or attachment. The user does not need to be online.

1. The watcher creates a `SourceEvent` containing the public URL, source system ID, content fingerprint, event time, and retrieval time.
2. A durable job graph stores the raw artifact, retrieves referenced source material within allowed access boundaries, and partitions work into extraction tasks.
3. The Multimodal Extractor processes agenda text, scanned pages, tables, and meeting media/transcript where available. It emits structured, source-cited `Decision`, `Commitment`, `ActionItem`, `SpeakerClaim`, and `OpenQuestion` objects.
4. The Entity Resolver links the new objects to known projects, places, public bodies, vendors, and existing cases. A low-confidence link is retained as a candidate, not accepted as fact.
5. The Evidence Graph updates the case state and asks the Delta Investigator whether the new record affects any existing commitment.
6. If a material, source-grounded change or absence is found, the system creates a `DecisionDelta` and stages a case in the editor inbox.
7. The editor opens the Decision Delta Studio, verifies the cited evidence across document, video/audio, map, timeline, and record views, then accepts, corrects, resolves, or requests more evidence.
8. If the editor approves an inquiry, the Artifact Worker creates a research packet and draft source question or records-request outline. The system never sends or files it automatically.

**Success state:** The editor has a trustworthy evidence bundle explaining what changed and the next verifiable question, without manually reconstructing the complete history.

### 9.2 Journey B: Meeting monitor produces a daily digital brief

**Trigger:** A new MPS Board or City public meeting recording, notice, final agenda, or minutes is discovered.

1. CivicTrace persists source metadata and allowed public media in Cloud Storage.
2. The Media Worker submits long audio to Google Cloud Speech-to-Text batch recognition and stores the asynchronous operation ID.
3. When a timestamped transcript is ready, Gemini through ADK extracts decision/action objects, vote/status language, promised milestones, speakers, and unresolved questions.
4. The Case Connector links new objects to relevant open Promise Ledger cases.
5. The Brief Builder creates a concise draft containing: What Changed, Promise Ledger Updates, Action Items, Evidence Clips, and Watch Next.
6. An editor reviews the brief, corrects any association using an in-context evidence control, and either publishes to an approved destination or retains it internally.

**Success state:** One source event yields a concise, reviewable public-interest brief and updates a long-lived accountability record.

### 9.3 Journey C: MPS Promise Ledger tracks public institutional evidence

**Trigger:** An MPS Board action, public school improvement-plan artifact, aggregate report-card update, public budget/facility artifact, or publicly available contract/award record enters the system.

1. The MPS adapter creates a case linked to an institution-level commitment.
2. The system reads the source carefully enough to identify what was committed, the named owner/body, stated timeline, public evidence expected later, and any limits of the record.
3. The case displays only public, aggregate institutional evidence. It excludes individual student information in every model input, index, log, export, and user view.
4. When a later public plan, Board update, or aggregate report-card source appears, the agent compares it to the original commitment without asserting causal conclusions.
5. The editor sees the exact source evidence and a narrow next question such as, “Has the district published the next promised plan-progress report?”

**Success state:** The product helps a reporter or community stakeholder follow a public school-system commitment across time without transforming students into data subjects.

---

## 10. Functional Requirements

### 10.1 Source Discovery and Ingestion

| ID | Requirement | Priority | Acceptance criteria |
|---|---|---:|---|
| **FR-01** | The system shall register public source adapters with source type, jurisdiction, refresh policy, terms/access notes, and parser version. | P0 | An adapter can be enabled/disabled and its last successful run is visible. |
| **FR-02** | The system shall discover new or changed public source items using source-specific IDs plus deterministic content fingerprints. | P0 | The same unchanged item is not processed twice; a changed item emits a new source event. |
| **FR-03** | The system shall persist raw source artifacts and metadata before AI extraction. | P0 | Every `Evidence` node resolves to immutable raw artifact metadata and hash. |
| **FR-04** | The system shall support HTML/JSON/CSV/PDF/image/audio/video metadata as public-source inputs. | P0 | The corpus manifest contains at least one structured record, one document, and one media-linked source. |
| **FR-05** | The system shall track source access failures and unavailable attachments as explicit states. | P0 | A missing artifact creates `NOT_PUBLISHED` or `REQUEST_NEEDED`, never fabricated text. |
| **FR-06** | The system shall preserve source retrieval timestamp, canonical URL, content hash, originating adapter, and relevant licensing/terms note. | P1 | All source cards show this information in a provenance inspector. |

### 10.2 Asynchronous Job Orchestration

| ID | Requirement | Priority | Acceptance criteria |
|---|---|---:|---|
| **FR-07** | The system shall use a durable event and task mechanism for all long-running ingestion and extraction work. | P0 | Closing the browser does not stop any active job. |
| **FR-08** | Each job shall have a stable idempotency key derived from source version, artifact hash, job type, and parser/model version. | P0 | A duplicate event completes without duplicate `Evidence` or output artifact. |
| **FR-09** | Jobs shall expose lifecycle states: `QUEUED`, `RUNNING`, `RETRYING`, `SUCCEEDED`, `FAILED`, `DEAD_LETTER`, and `CANCELLED`. | P0 | State transitions are visible in the audit timeline. |
| **FR-10** | The system shall retry transient errors and route terminal failures to a dead-letter queue with sufficient diagnostic context for manual replay. | P1 | A controlled failure can be replayed from an editor/developer-only recovery interface. |
| **FR-11** | The system shall support a historical backfill manifest and later incremental processing. | P0 | A fresh environment can replay a documented corpus without source-specific manual steps. |

### 10.3 Multimodal Extraction and Evidence Modeling

| ID | Requirement | Priority | Acceptance criteria |
|---|---|---:|---|
| **FR-12** | Gemini through ADK shall extract typed objects from public documents and transcript/media context using structured schemas. | P0 | Each object validates against schema and carries source anchors. |
| **FR-13** | Extracted object classes shall include `Commitment`, `Decision`, `ActionItem`, `Vote`, `SpeakerClaim`, `Project`, `Vendor`, `Place`, `Evidence`, `Unknown`, `Conflict`, and `Inquiry`. | P0 | A real demo case uses at least `Commitment`, `Decision`, `Place`, `Evidence`, `Unknown`, and `Inquiry`. |
| **FR-14** | An evidence anchor shall support page, table-cell/row, transcript offset, video/audio timestamp, JSON field/row, or geographic feature location. | P0 | Every Decision Delta claim displays an actionable anchor. |
| **FR-15** | The model shall use bounded, case-relevant retrieval rather than place the entire corpus in a context window. | P0 | The code and architecture document show prefiltering and source selection. |
| **FR-16** | Entity resolution shall distinguish confirmed matches from candidates and uncertainty. | P0 | A wrong/candidate association can be corrected by a user and never silently becomes a confirmed fact. |

### 10.4 Promise Ledger and Decision Delta

| ID | Requirement | Priority | Acceptance criteria |
|---|---|---:|---|
| **FR-17** | A Promise Ledger case shall record the original public commitment, owner/public body, location/entity, date, stated timeline, expected evidence, and cited supporting sources. | P0 | The case opens with a source-grounded commitment card rather than AI prose alone. |
| **FR-18** | The Delta Investigator shall compare new evidence to case state and only create a material Decision Delta when it can cite an original and a later evidence anchor. | P0 | Automated grounding test fails if either anchor is absent. |
| **FR-19** | A Decision Delta shall contain: supported change, original evidence, later evidence, unresolved question, confidence/uncertainty status, and proposed next evidence. | P0 | Each field appears in the Decision Delta Studio. |
| **FR-20** | The system shall represent contradictory source statements as `CONFLICTING`, with both sources preserved. | P0 | Contradictory fixture never collapses into a single asserted conclusion. |
| **FR-21** | The system shall permit a user to resolve, defer, follow, or mark a case as needing more evidence. | P1 | Case status updates are recorded as ledger events. |

### 10.5 Inquiry, Approval, and Publication Controls

| ID | Requirement | Priority | Acceptance criteria |
|---|---|---:|---|
| **FR-22** | The planner may propose a bounded next question, missing record, or records-request outline based on a case’s explicit uncertainty. | P0 | Proposed inquiry lists the source gap it would address. |
| **FR-23** | The system shall require a case-bound, expiring human approval token before a worker can create an external-ready artifact or send data to a configured destination. | P0 | Unauthorized action test fails closed. |
| **FR-24** | The artifact worker shall assemble a research packet containing chronology, source links, relevant excerpts, timestamp clips, uncertainty state, and draft question. | P0 | One complete packet is generated in the live demo. |
| **FR-25** | Publication integrations shall be optional and default to draft-only. | P1 | No public post can occur without explicit user approval in the current session. |

### 10.6 Meeting Monitor and Digital Brief

| ID | Requirement | Priority | Acceptance criteria |
|---|---|---:|---|
| **FR-26** | The system shall discover monitored meeting notices, agendas, recordings, and final minutes through source-specific adapters. | P1 | One City and one MPS source event can be replayed. |
| **FR-27** | Long public meeting audio shall be processed asynchronously through Cloud Storage and Speech-to-Text batch recognition. | P1 | Operation ID, transcription state, transcript, and time anchors are persisted. |
| **FR-28** | The brief builder shall create What Changed, Promise Ledger Updates, Action Items, Evidence Clips, and Watch Next sections. | P1 | A human reviewer can edit, approve, or discard the brief. |
| **FR-29** | Meeting facts shall update existing open cases when linked evidence supports the association. | P1 | A meeting event visibly updates an existing Promise Ledger case. |

---

## 11. User Experience Requirements

### 11.1 Design objective

The CivicTrace user interface must feel like an **evidence studio**, not a chat app and not a generic government dashboard. Its central user question is: **“Can I personally verify why the system says this changed?”**

![CivicTrace Promise Ledger flow](assets/civictrace_promise_ledger_flow.png)

The flow above makes the product boundary explicit: source comparison may create an evidence-linked Decision Delta, but human review controls external inquiry or publication. Corrections feed back into case state and determine the next source to watch.

### 11.2 Decision Delta Studio

| Surface | Requirement | User value |
|---|---|---|
| **Case header** | Displays case title, jurisdiction, current status, materiality label, last evidence update, and confidence/uncertainty indicator. | Allows fast editorial triage without hiding ambiguity. |
| **Promise card** | Shows original commitment language with a clickable document page/table/vote source anchor. | Establishes what was actually promised. |
| **Evidence timeline** | Presents chronological source cards from first commitment through current record, including gaps and pending expected evidence. | Makes long-lived accountability understandable. |
| **Media inspector** | Synchronizes a video/audio player, timestamped transcript, agenda/document page, and extracted fact. | Enables quick verification of context and language. |
| **Place canvas** | Displays project location, district/parcel or contextual map feature, and related public data layers where available. | Connects policy language to public geography. |
| **Evidence graph** | Shows entities and provenance edges; visually distinguishes supported links, candidate links, conflict, and missing evidence. | Makes the system’s reasoning inspectable rather than mysterious. |
| **Challenge mode** | Allows the reviewer to ask “What would change this conclusion?” and to correct a source/entity association. | Captures feedback and preserves intellectual humility. |
| **Inquiry drawer** | Displays proposed next record/question, justification, approval control, and resulting packet. | Converts observation into bounded, reviewable action. |

### 11.3 Multimodal interaction requirements

The multimedia experience must be materially useful. A user must be able to open a page containing a public commitment, jump to the relevant audio/video time, inspect the structured record or map tied to the same entity, correct an association, and see the timeline/graph update. Text alone cannot satisfy this requirement because the meaning of a public decision may live in a table, a location, a timestamped qualification in speech, or the absence of an expected attachment.

### 11.4 Accessibility requirements

The product shall provide keyboard navigation, transcript text for audio/video, visible source labels, high-contrast status indicators that do not rely on color alone, accessible document links, and a non-autoplay default for media. The system shall make clear that AI-generated extracts are derived evidence and should not replace the original source.

---

## 12. MPS Education Accountability Domain Requirements

### 12.1 Domain purpose

The MPS extension is a public institutional-accountability domain pack. It follows public Board commitments through public improvement plans, public budget/facility/contract artifacts, and publicly reported aggregate outcomes. It is neither a student-support product nor a system for evaluating or ranking individual students, teachers, or schools.

### 12.2 Data eligibility matrix

| Data category | Allowed? | Reason |
|---|---|---|
| Public MPS Board agendas, minutes, meeting audio/video, and policy documents | Yes | Public institutional decision evidence. |
| Public school improvement-plan summaries and district/state report cards | Yes | Public, aggregate institutional plan/outcome material. |
| Public budget, facility, procurement, award, or executed-contract artifact | Yes, where lawfully public | Implementation and resource evidence. |
| Aggregate school/district performance or accountability indicator | Yes | Publicly reported outcome context; must not imply causality. |
| Individual student records, attendance, grades, discipline, disability, health, addresses, family details, or profiles | No | Privacy, safety, and mission boundary. |
| Predictive student risk/intervention model | No | Outside scope and inconsistent with institutional-transparency purpose. |

### 12.3 MPS Promise Ledger acceptance test

A valid MPS case must contain: one public Board or institutional commitment; one linked public implementation artifact; one publicly available aggregate outcome/progress artifact or explicit unknown; and a source-grounded, human-reviewed next question. The system may state that evidence appears in sequence; it may not assert that one action caused a reported outcome without a valid source establishing causality.


---

## 13. Technical Architecture

### 13.1 Architectural objective

CivicTrace must prove that it can handle a long-running public-data workflow safely. The architecture separates source retrieval, raw preservation, model reasoning, deterministic state changes, and external side effects. The model is never the sole authority over persistence, publication, or outreach.

![CivicTrace competition architecture](assets/civictrace_competition_architecture.png)

### 13.2 Proposed Google Cloud stack

| Layer | Service | Responsibility | Rationale |
|---|---|---|---|
| **Application/API** | Cloud Run | Hosts source-watch API, query API, case actions, and user-facing service endpoints. | Serverless deployment with scale-to-zero behavior and visible Cloud proof. |
| **Scheduling** | Cloud Scheduler | Triggers periodic adapter checks for sources that do not provide push notifications. | Makes monitoring autonomous and auditable. |
| **Event fabric** | Pub/Sub | Carries `SourceDiscovered`, `ArtifactStored`, `ExtractionRequested`, `CaseUpdated`, and similar events. | Decouples source discovery from downstream workers. |
| **Durable jobs** | Cloud Tasks | Executes idempotent extraction, transcription, linking, and artifact jobs with controlled retries/rate limits. | Supports long-running, recoverable background work. |
| **Raw artifacts** | Cloud Storage | Stores immutable source snapshots, documents, media metadata, transcripts, and generated inquiry packets. | Preserves primary evidence and enables replay. |
| **Operational case state** | Firestore | Stores case state, evidence ledger, jobs, approvals, user corrections, and lightweight graph edges. | Simple persistent state that supports real-time product views. |
| **Corpus-scale analytics** | BigQuery | Stores high-volume tabular public records and supports source/date-partitioned filtering and aggregation. | Keeps large public datasets out of model context windows. |
| **Agent orchestration** | Google ADK | Coordinates typed extraction, retrieval, Delta Investigator, and Inquiry Planner agents. | Satisfies required agent framework and supports explicit tool boundaries. |
| **Models** | Gemini 3.5 Flash or newer via Vertex AI or Gemini API | Extracts structured evidence, compares sources, reasons over multimodal material, and proposes bounded next steps. | Meets required Gemini usage and supports fast structured reasoning. |
| **Meeting transcription** | Cloud Speech-to-Text batch recognition | Transcribes stored public meeting audio asynchronously. | Fits the media worker and Google Cloud story. [12] |
| **Observability** | Cloud Logging and Cloud Trace | Records source/job lineage, failures, retries, approvals, and completion state. | Makes fault tolerance visible to judges and maintainers. |
| **Secret and access control** | Secret Manager, IAM service accounts | Separates adapter credentials/configuration and scopes worker permissions. | Limits unintended tool/data access. |

### 13.3 Event flow

1. A scheduled or notification-driven adapter checks an approved public source.
2. When the source fingerprint differs from the last recorded version, the adapter emits a `SourceDiscovered` event.
3. The Ingest API writes source metadata and raw content to Cloud Storage, then emits `ArtifactStored`.
4. Cloud Tasks creates idempotent work for parsing, extraction, entity resolution, and graph update.
5. Gemini + ADK extract typed facts with evidence anchors. Deterministic schema validators reject malformed objects.
6. The graph update worker appends source-linked ledger events and updates materialized case state in Firestore.
7. The Delta Investigator retrieves only relevant case/source context and creates a Decision Delta only if it has the required evidence anchors.
8. The Inquiry Planner proposes a narrow, case-bound next step. It cannot directly publish, send messages, or submit records requests.
9. A reviewer approves or rejects the proposed action. The approval token binds the case, artifact hash, action type, recipient/destination where applicable, and expiry.
10. The Artifact Worker renders the evidence packet; optional publication remains draft-only until an explicit reviewer approval.

### 13.4 Architecture decision records

| Decision | Rationale | Trade-off |
|---|---|---|
| **Use raw artifact storage before extraction** | Guarantees provenance, replay, and model-output auditability. | Increases storage management and requires retention policy. |
| **Use BigQuery for high-volume public rows and Firestore for case state** | Separates analytical scale from low-latency case interaction. | Requires a clear contract for synchronized identifiers. |
| **Use a typed graph model rather than unrestricted model memory** | Forces facts, unknowns, conflicts, and citations into inspectable structures. | Requires domain schema work and careful extraction evaluation. |
| **Use at-least-once event delivery plus idempotency** | Real public feeds and queues can duplicate events; correctness is safer than assuming exactly-once delivery. | Requires stable keys and terminal-state design. |
| **Require approval tokens for side effects** | Preserves human authority and reduces harm from agent mistakes. | Adds a review step that is intentionally not automated away. |
| **Use Speech-to-Text batch plus Gemini extraction for meeting media** | Separates reliable timestamped transcription from semantic analysis and preserves an asynchronous workflow. | Adds an operation/polling state to manage. |
| **Build City-first, MPS second** | Protects the core demo from adapter sprawl while demonstrating platform extensibility. | MPS is a short extension rather than the central hackathon loop. |

---

## 14. Data Model and Contracts

### 14.1 Core entities

| Entity | Purpose | Required fields |
|---|---|---|
| `Source` | Defines a monitored public system/adapter. | `source_id`, `jurisdiction`, `adapter_type`, `canonical_url`, `refresh_policy`, `terms_note`, `status` |
| `SourceEvent` | Represents a discovered/changed source version. | `event_id`, `source_id`, `external_id`, `fingerprint`, `detected_at`, `source_url`, `event_type` |
| `Artifact` | Immutable raw object stored or referenced by the system. | `artifact_id`, `source_event_id`, `content_hash`, `mime_type`, `storage_uri`, `retrieved_at`, `metadata` |
| `Evidence` | A source-anchored extract from an artifact. | `evidence_id`, `artifact_id`, `anchor_type`, `anchor_value`, `verbatim_excerpt`, `extraction_confidence`, `status` |
| `Claim` | A source-supported statement that is not necessarily a commitment. | `claim_id`, `text`, `evidence_ids`, `status`, `time_range` |
| `Commitment` | A public promise, decision, expected milestone, or stated action. | `commitment_id`, `text`, `owner_entity_id`, `date`, `expected_evidence`, `evidence_ids`, `case_id` |
| `Decision` | An institutional action such as pass/defer/amend/vote. | `decision_id`, `body`, `status`, `vote`, `date`, `evidence_ids`, `related_commitment_ids` |
| `Entity` | Canonical public body, person acting in official role, project, vendor, place, school, or other public object. | `entity_id`, `entity_type`, `canonical_name`, `aliases`, `match_status`, `source_evidence_ids` |
| `Case` | Long-lived accountability unit. | `case_id`, `title`, `jurisdiction`, `status`, `topic`, `entity_ids`, `commitment_ids`, `last_updated` |
| `DecisionDelta` | A grounded, material change or explicit unresolved gap. | `delta_id`, `case_id`, `original_evidence_ids`, `later_evidence_ids`, `summary`, `uncertainty_state`, `next_evidence_needed` |
| `Inquiry` | Proposed human-reviewed question/record request. | `inquiry_id`, `case_id`, `question`, `justification_evidence_ids`, `approval_status`, `artifact_id` |
| `Job` | Durable background-work record. | `job_id`, `idempotency_key`, `job_type`, `state`, `attempt_count`, `input_refs`, `output_refs`, `trace_id` |
| `Approval` | Explicit permission for a bounded external-ready artifact or publication action. | `approval_id`, `case_id`, `action_type`, `artifact_hash`, `approved_by`, `expires_at`, `status` |

### 14.2 Evidence and uncertainty states

| State | Meaning | UI behavior |
|---|---|---|
| `SUPPORTED` | Evidence directly supports the displayed fact or relationship. | Standard source-backed presentation. |
| `CANDIDATE_LINK` | Possible entity/project match awaiting user confirmation or stronger evidence. | Visually distinct; never treated as confirmed. |
| `CONFLICTING` | Credible sources express materially different facts or interpretations. | Display both anchors and prompt review. |
| `NOT_PUBLISHED` | Expected public record/attachment is not available. | Treat as visible gap, not a negative fact. |
| `REQUEST_NEEDED` | The system can articulate a narrow source gap and proposed inquiry. | Present approval action. |
| `HUMAN_REVIEW` | Materiality, identity, or implication requires a human judgment. | Block any outward-facing artifact from being finalized. |
| `RESOLVED` | Reviewer closed a case with rationale or sufficient evidence. | Preserve history; remove from active alert queue. |

### 14.3 Structured output contracts

All Gemini/ADK workers must emit schema-validated JSON or Pydantic-equivalent objects. Free-form model narrative may be stored as a draft explanation but never becomes authoritative state without a valid evidence-linked object. Schema validation, source-anchor validation, and approval checks must execute outside the model.

---

## 15. AI, Retrieval, and Evaluation Design

### 15.1 Agent roles

| Agent / worker | Inputs | Permitted output | Prohibited behavior |
|---|---|---|---|
| **Multimodal Extractor** | Raw artifact, bounded extraction prompt, source metadata. | Typed evidence, decisions, commitments, facts, and anchors. | Inventing unavailable text or converting uncertainty to fact. |
| **Entity Resolver** | Candidate entities, place/vendor/project fields, source evidence. | Confirmed or candidate links with confidence and rationale. | Silent identity merging without evidence. |
| **Graph Updater** | Validated typed objects and ledger state. | Deterministic node/edge changes and ledger events. | Model-led database writes outside contract validation. |
| **Delta Investigator** | Open case, original commitments, selected later evidence. | Decision Delta or no-delta result with source references. | Material change assertion without original and later anchors. |
| **Inquiry Planner** | Case uncertainty and evidence gap. | Narrow question, expected record, and rationale. | Filing requests, contacting sources, or publishing. |
| **Brief Builder** | Validated meeting facts and updated cases. | Draft five-section brief with citations. | Publishing without human approval. |

### 15.2 Retrieval strategy

CivicTrace uses a layered retrieval approach. BigQuery first limits structured public records by jurisdiction, date, entity, address/project key, and source type. Firestore case state identifies active commitments and entities. A vector/retrieval layer then selects the smallest relevant set of document chunks, transcript segments, or media descriptions. Gemini receives this bounded evidence bundle plus explicit instructions to preserve uncertainty and emit source anchors.

This strategy prevents the common failure mode of treating an LLM context window as a civic database. It also supports a demonstrable architecture decision: **data is filtered deterministically before it is interpreted probabilistically.**

### 15.3 Evaluation suite

| Evaluation | Test | Pass criteria |
|---|---|---|
| **Grounding** | Each Decision Delta contains original and later evidence anchors. | 100% pass for displayable deltas. |
| **Faithfulness** | Extracted text is checked against source excerpt/location. | Mismatched quote/anchor is rejected. |
| **Missingness** | A missing source fixture is processed. | Result is `NOT_PUBLISHED` or `REQUEST_NEEDED`; no generated filler. |
| **Conflict** | Two conflicting public statements are ingested. | Both sources remain visible as `CONFLICTING`. |
| **Idempotency** | Same `SourceEvent` delivered twice. | One terminal evidence result and one user-visible state change. |
| **Approval gate** | Artifact/publication action invoked without token. | Action is blocked and audit event recorded. |
| **Entity correction** | Reviewer rejects a candidate link. | Future retrieval/ranking respects correction for the case. |
| **Media alignment** | Meeting clip transcript anchor is opened. | UI retrieves the correct timestamp and associated transcript context. |

### 15.4 Model safety and prompt requirements

Prompts must state that the system works from public evidence, that it must not allege wrongdoing or infer causality, that it must distinguish direct support from candidate association, and that a missing record is not proof of a negative conclusion. Prompts should request a concise rationale only when it can cite evidence IDs; chain-of-thought-like internal reasoning must not be displayed or treated as an audit log. The durable audit record is the evidence ledger, job trace, schema outputs, and human approval history.

---

## 16. Security, Governance, Privacy, and Editorial Integrity

### 16.1 Source and data governance

CivicTrace will ingest only public sources or sources for which the authorized organization has a right to use the information. Each adapter must record access/terms notes. The product must honor source rate limits, avoid bypassing access controls, preserve source URLs, and make it clear when an artifact is an archived copy rather than a current canonical record.

### 16.2 Human authority model

| Action | Agent may prepare? | Agent may execute automatically? | Required control |
|---|---:|---:|---|
| Retrieve permitted public source | Yes | Yes, through scoped adapter | Adapter allowlist, rate limits, source terms. |
| Extract/summarize source evidence | Yes | Yes | Schema validation and provenance. |
| Update internal evidence graph | Yes, via validated worker | Yes | Idempotency, audit ledger, typed schemas. |
| Propose an inquiry question | Yes | Yes, as draft only | Human review. |
| Render research packet | Yes | Yes, after case/approval policy | Case-bound action permission. |
| Send email, file records request, contact source | Yes, as draft | No | Explicit user approval with target/action binding. |
| Publish meeting brief or public claim | Yes, as draft | No | Editor approval, version review, destination-specific control. |

### 16.3 MPS safety boundary

The MPS extension must operate on public institutional evidence only. It may discuss a published plan, public Board decision, public contract, public facility project, or public aggregate report-card data. It may not ingest or infer student-level attendance, educational record, disability, disciplinary, health, family, address, or other personally identifying/sensitive information. It may not produce student profiles, risk scores, intervention recommendations, or claims about individual educators/students.

### 16.4 Editorial integrity requirements

Every public-facing draft must label itself as **AI-assisted, source-grounded draft requiring human editorial review** until approved. The user interface must make uncertainty and source provenance more prominent than model-written prose. The system must never use a confidence score as a substitute for source verification.

---

## 17. Reliability, Observability, and Cost Control

### 17.1 Reliability requirements

The production architecture must tolerate rate limits, temporary source failures, duplicate delivery, scanner/OCR problems, transcription delays, model timeouts, and partial data. A failure in one artifact must not corrupt the case or force an entire corpus replay. Every job must emit traceable status transitions and preserve recoverable context.

### 17.2 Observability requirements

| Signal | Purpose |
|---|---|
| Source run duration and changed-item count | Proves watcher health and update volume. |
| Queue depth, task latency, retry count, and dead-letter count | Proves asynchronous operational health. |
| Artifact parse/extraction success rate | Reveals source format regressions. |
| Grounding/evaluation failures | Identifies unsafe model output or schema drift. |
| Case updates and Decision Delta volume | Indicates product usefulness, not merely processing volume. |
| Approval and publication actions | Supports editorial audit and accountability. |
| Per-source/model/storage cost | Enables budget control and low-cost scaling. |

### 17.3 Cost-control principles

Use Gemini Flash for extraction and lightweight reasoning, reserve more expensive model usage only for a narrow final comparison if demonstrably necessary, cache artifact fingerprints and embeddings, process incrementally, partition large datasets, set Cloud Run minimum instances to zero, cap queue concurrency, enforce budget alerts, and retain only the source artifacts necessary for product/replay obligations. The hackathon resources recommend Gemini Flash first, scale-to-zero services, minimal initial provisioning, strict instance caps, lightweight storage, and budget alerts. [2]


---

## 18. Implementation Plan

### 18.1 Workstreams

| Workstream | Scope | P0 output |
|---|---|---|
| **Public-source adapters** | Milwaukee City Legistar, City CKAN catalog/datasets, curated financial corroboration source, and replay corpus manifest. | One reliable source-change event produces raw source artifacts. |
| **Evidence platform** | Cloud Storage vault, Firestore ledger, schemas, BigQuery table setup, basic entity resolver. | A replayed source creates source-linked structured evidence. |
| **Agent workflow** | ADK extractor, Delta Investigator, Inquiry Planner, approval flow. | A case produces one grounded Decision Delta and staged inquiry. |
| **Evidence Studio** | Timeline, document/PDF/table inspector, map/place view, media clip/transcript view, graph, approval drawer. | A reviewer can verify and correct one case end-to-end. |
| **Reliability and tests** | Job lifecycle, idempotency, missingness/conflict fixture, logs/traces, local replay command. | Duplicate and missing-source demonstrations pass. |
| **MPS extension** | One Board/IC Board meeting source, batch transcription, public plan/report-card link, MPS brief. | A short cross-institution extension run updates an MPS case. |
| **Submission package** | README, architecture diagram, architecture decision records, video, deployment proof, Devpost narrative. | A judge can understand and reproduce the product without assistance. |

### 18.2 Recommended execution sequence

| Order | Build increment | Definition of done |
|---:|---|---|
| **1** | Establish project skeleton, schemas, Firestore, Cloud Storage, and one corpus manifest. | Raw source is persisted with hash and provenance. |
| **2** | Build one Milwaukee City Legistar adapter and event replay path. | New/changed event reliably emits an idempotent job. |
| **3** | Build document extraction and evidence cards. | One agenda/document generates typed, cited commitments/decisions. |
| **4** | Build the Promise Ledger and Decision Delta rule. | Original and later source create a grounded delta or explicit no-delta result. |
| **5** | Build inquiry packet and approval gate. | Reviewer approval produces a complete, source-cited artifact. |
| **6** | Build Decision Delta Studio with PDF/table, timeline, map, and graph. | User verifies every displayed claim from its source anchor. |
| **7** | Add asynchronous meeting pipeline and transcript/media view. | A public meeting recording yields a timestamped, cited update. |
| **8** | Add duplicate/missingness/failure fixtures, traces, and deploy to Cloud Run. | Architecture can be proved under failure in the recording. |
| **9** | Add a compact MPS extension only after City loop is stable. | One MPS source refresh updates a public institutional case. |
| **10** | Record four-minute video; publish repository documentation and optional build post/social post. | Submission is complete before deadline. |

### 18.3 Suggested team roles

A single builder can deliver the narrow MVP, but a small team can parallelize clearly.

| Role | Main responsibility |
|---|---|
| **Product / civic research lead** | Selects the historical case, validates source chronology, defines editorial boundary, and writes the product narrative. |
| **Agent/backend engineer** | Implements adapters, job orchestration, schemas, ADK workers, approval flow, and Google Cloud deployment. |
| **Data/evaluation engineer** | Builds corpus manifest, BigQuery transformations, entity-resolution tests, grounding tests, and reliability fixtures. |
| **Product designer / frontend engineer** | Builds Evidence Studio, timeline, media inspector, map/graph interaction, accessibility, and demo polish. |
| **Editorial / community advisor** | Validates that briefs and inquiry packets are useful, careful, and non-defamatory. |

---

## 19. Risk Register and Mitigation Plan

| Risk | Likelihood | Impact | Mitigation |
|---|---|---:|---|
| A live City/MPS page changes or rate-limits during demo | Medium | High | Use a lawful, documented replay corpus with real public-source snapshots; show live system processing the replay event. |
| Meeting attachment/video is unavailable | High | Medium | Treat missingness as a first-class `NOT_PUBLISHED` / `REQUEST_NEEDED` outcome; show this in the demo. |
| Dynamic procurement/open-checkbook portal is difficult to automate | High | Medium | Use a public exported/captured record as a seeded corroboration source; do not make it P0. |
| Entity matching connects the wrong project/vendor/place | Medium | High | Preserve candidate links, show confidence/anchor evidence, require confirmation for material association, enable correction. |
| Model produces unsupported inference | Medium | High | Require source-anchor validation; use two-anchor minimum for Decision Delta; fail closed to human review. |
| CivicTrace is mistaken for an allegation/corruption tool | Medium | High | Use neutral language: promise, record, change, unknown, next evidence; do not assign blame or causal conclusions. |
| MPS scope introduces privacy concerns | Medium | High | Enforce public institutional data-only allowlist; do not ingest student-level records or create student profiles. |
| Architecture becomes overbuilt for the hackathon | High | High | Enforce P0 City loop first; MPS and live procurement are P1/P2 extensions. |
| Multimodal UX becomes a chat façade | Medium | Medium | Require synchronized source evidence surfaces and correction controls; do not use a chat window as the core demo. |
| Judges cannot understand technical sophistication quickly | Medium | High | Use the four-minute proof script, visible job states, duplicate replay, missingness, Cloud console, and simple architecture diagram. |

---

## 20. Hackathon Submission Plan

### 20.1 Required assets

| Asset | CivicTrace content |
|---|---|
| **Track selection** | The Taskmaster |
| **Hosted project** | Cloud Run-hosted Evidence Studio and/or authenticated demonstration URL |
| **Project description** | Problem, Promise Ledger workflow, source scope, user safety boundaries, technologies, findings, and learning |
| **Repository** | Public or private repository with access granted to the required judge accounts if private |
| **README / spin-up instructions** | Local corpus replay, environment setup, Cloud deployment, source terms notes, test command, known limitations |
| **Architecture diagram** | Rendered diagram plus Mermaid source showing source adapters, durable jobs, agent workers, state, approval boundary, and observability |
| **Demo video** | Four-minute unedited proof of source event, asynchronous processing, Evidence Studio, approval packet, resilience test, and Google Cloud deployment |
| **Optional bonus contributions** | Public build article and qualifying social post; carefully justified additional Google model integration only if it adds real product value |

### 20.2 Four-minute video structure

1. **0:00–0:20 — Friction.** “Public promises are made in meetings and buried across years of records.” Show corpus coverage and an empty/updated case.
2. **0:20–0:45 — Autonomous trigger.** Re-emit a real Milwaukee public-source change; show durable background job fan-out.
3. **0:45–1:20 — Heavy lifting.** Show artifact storage, document/media extraction, entity resolution, graph update, and real job state.
4. **1:20–2:05 — Multimodal verification.** Open the Decision Delta Studio and synchronize source document, hearing clip, map, timeline, and graph.
5. **2:05–2:35 — Completed workflow.** Show proposed question, approval, and generated inquiry packet.
6. **2:35–3:15 — Architectural proof.** Replay duplicate event and show single result; process missing attachment and show explicit uncertainty state.
7. **3:15–3:40 — Cloud proof.** Show Cloud Run, queue/event infrastructure, Firestore/Storage/BigQuery, and trace/log view.
8. **3:40–4:00 — Close.** “CivicTrace does not publish a claim. It makes the next verifiable question impossible to miss.”

### 20.3 Devpost project-description skeleton

**Problem.** Local public decisions are distributed across meetings, data systems, documents, video, and time. Resource-strapped local reporting and civic organizations cannot continuously follow every promise from vote to public outcome.

**Solution.** CivicTrace is an approval-gated public-evidence agent. It monitors selected Milwaukee public sources, preserves raw evidence, builds a durable Promise Ledger, detects source-grounded changes, and creates inquiry-ready case files. The system is designed to prepare work, not make allegations or publish without human review.

**Why Taskmaster.** A public source change triggers a complete asynchronous workflow: source retrieval, multimodal extraction, entity resolution, persistent case update, Decision Delta detection, and a human-approved inquiry packet.

**Technology.** Gemini 3.5 Flash or newer, Google ADK, Cloud Run, Pub/Sub, Cloud Tasks, Cloud Storage, Firestore, BigQuery, Cloud Speech-to-Text, Cloud Logging, and Cloud Trace.

**Safety.** CivicTrace operates on public institutional records, preserves provenance and uncertainty, gates all external action by human approval, and excludes student-level MPS data.

---

## 21. Project Proposal: Why CivicTrace Can Become a Real Product

### 21.1 Opportunity

CivicTrace addresses a durable structural problem: public institutions produce an expanding volume of public material, while the people expected to make sense of it—local reporters, community information organizations, civic researchers, and residents—have diminishing time and institutional support. The local-news decline is a visible manifestation of this capacity gap. [4] CivicTrace is a force multiplier for careful human oversight, not an attempt to automate it away.

### 21.2 Beachhead market

The immediate beachhead is a Milwaukee-area news/civic partner that needs a persistent City Council/committee and MPS Board monitor. The partner receives a defined set of source adapters, a shared public-evidence workspace, a review inbox, and inquiry packets. Milwaukee is strategically suitable because it is both technically feasible and authentically local to the product thesis; the pilot can demonstrate a template for other municipalities without pretending that every city is identical.

### 21.3 Customer segments and value proposition

| Segment | Buyer / sponsor | Value proposition |
|---|---|---|
| **Local newsroom** | Editor, investigations lead, publisher, nonprofit news executive | Extends a small civic beat with persistent source monitoring and a source-verifiable case memory. |
| **Public-interest nonprofit** | Research director, advocacy lead, civic-information program | Turns public commitments into transparent, shared evidence work without relinquishing human judgment. |
| **University reporting/civic-tech lab** | Program director, faculty lead | Provides an auditable research platform for students/documenters and community collaboration. |
| **Community information network** | Neighborhood news cooperative, resident-documentation group | Makes meeting observation and public records easier to connect to an ongoing public narrative. |
| **District transparency partner** | Public-information/transparency team, parent/community coalition | Follows public MPS commitments and aggregate outcomes while respecting student privacy. |

### 21.4 Business model hypothesis

The initial offering can be a subscription or sponsored territory license that includes configured source adapters, a defined case/corpus allowance, user seats, and support. Higher tiers can add jurisdiction packs, deeper historical backfills, custom evidence schemas, partner integrations, and privacy/compliance configuration. The defensible asset is not a general model; it is the combination of jurisdiction-specific source adapters, time-aware provenance graph, editorial workflow, correction history, and trusted public-evidence corpus.

### 21.5 Expansion roadmap

| Horizon | Expansion |
|---|---|
| **Pilot** | Milwaukee City Promise Ledger with one partner and one bounded public-project class. |
| **Domain proof** | Add MPS public institutional records and one education-accountability case. |
| **Regional platform** | Milwaukee County adapter and additional City departments/records where the public source path is stable. |
| **Repeatable product** | Source-adapter templates for Legistar, IC Board, CKAN, Socrata, common meeting platforms, and public document repositories. |
| **Network product** | Multi-territory newsroom/nonprofit consortium with shared but jurisdiction-separated public-source infrastructure. |

---

## 22. Final Go/No-Go Decision

**Go.** CivicTrace is ambitious enough to push agentic technology beyond chat, but narrow enough to deliver a real end-to-end proof. The product wins by showing persistent state, multimodal evidence grounding, event-driven background work, failure-aware architecture, and a concrete public-interest artifact. Milwaukee supplies a credible first territory. MPS supplies a high-value, privacy-safe vertical extension. The winning discipline is to make one Promise Ledger loop flawless before adding more sources, more jurisdictions, or more automation.

> **Final product statement:** *CivicTrace gives communities a durable memory of what public institutions promised, what the public record later shows, and the next verifiable question no one has capacity to stop asking.*

---

## References

[1]: https://allthingsagentichackathon.devpost.com/ "All Things Agentic Hackathon — official overview"

[2]: https://allthingsagentichackathon.devpost.com/resources "All Things Agentic Hackathon — official resources and track definitions"

[3]: https://allthingsagentichackathon.devpost.com/rules "All Things Agentic Hackathon — official rules, judging, and prizes"

[4]: https://localnewsinitiative.northwestern.edu/projects/state-of-local-news/2024/report/ "Northwestern Medill — The State of Local News: 2024"

[5]: https://www.brookings.edu/wp-content/uploads/2018/09/WP44.pdf "Gao, Lee, and Murphy — Financing Dies in Darkness? The Impact of Newspaper Closures on Public Finance"

[6]: https://data.milwaukee.gov/ "City of Milwaukee Open Data Portal"

[7]: https://milwaukee.legistar.com/Calendar.aspx "City of Milwaukee — Legistar calendar"

[8]: https://milwaukeecounty.legistar.com/Calendar.aspx "Milwaukee County — Legistar calendar"

[9]: https://biglocalnews.org/content/news/2023/06/23/welcome-to-agenda-watch.html "Big Local News — Welcome to Agenda Watch"

[10]: https://www.milwaukeepublicschools.org/about/board "Milwaukee Public Schools — Board of School Directors"

[11]: https://www.milwaukeepublicschools.org/about/directory/academics/research-assessment-data/performance-improvement "Milwaukee Public Schools — School Performance and Improvement"

[12]: https://docs.cloud.google.com/speech-to-text/docs/batch-recognize "Google Cloud Speech-to-Text — Transcribe long audio files into text"

[13]: https://www.milwaukeepublicschools.org/about/directory/finance/procurement-risk-management/vendors/bids-rfps "Milwaukee Public Schools — Bids and RFPs"

[14]: https://data.county.milwaukee.gov/ "Milwaukee County Open Data Portal"

[15]: https://stories.opengov.com/milwaukee/published/T2SmXmV8p "City of Milwaukee — Open Checkbook"
