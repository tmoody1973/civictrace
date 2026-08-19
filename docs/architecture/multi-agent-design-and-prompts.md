# CivicTrace Multi-Agent Architecture and System Prompts

## 1. Answer: Yes, but the Orchestrator Must Be Constrained

**Yes. CivicTrace should be a multi-agent application with an orchestrator, but the orchestrator must not be a free-form “super-agent.”** The core architecture is a **deterministic, event-driven workflow orchestrator** that invokes narrowly scoped agents at the right moment, validates their structured outputs, persists durable state, and requires human approval before any external-facing action.

The orchestrator is the system’s operating system, not its investigator. It decides **which work may run, in what order, against which case, with which data and tool permissions**. It does not make civic claims, infer wrongdoing, write directly to the evidence graph, publish a brief, contact a source, or submit a public-records request.

> **Design rule:** Models may reason over bounded evidence. Deterministic services own state changes, permissions, retries, and side effects.

This design is more robust than a single general agent because public-interest work must preserve provenance, uncertainty, and editorial control. It also makes the hackathon architecture immediately legible: the product has autonomous work, durable state, specialized agents, fault tolerance, and a hard approval boundary.

## 2. Control Plane vs. Intelligence Plane

| Layer | Components | Authority | Must never do |
|---|---|---|---|
| **Control plane** | Source scheduler, Cloud Run orchestration API, Pub/Sub, Cloud Tasks, schema validator, Firestore ledger, approval service, policy engine, job recovery service. | Routes work, tracks state, validates contracts, enforces idempotency, controls permissions. | Invent evidence, make substantive civic claims, choose political framing, or publish autonomously. |
| **Intelligence plane** | Document Evidence Agent, Media Evidence Agent, Entity Resolution Agent, Case Linker, Delta Investigator, Inquiry Planner, Brief Builder, Quality Reviewer. | Extracts, compares, classifies, proposes, and drafts within a bounded evidence package. | Bypass schema validation, mutate state directly, use unapproved sources, or initiate external contact. |
| **Human authority plane** | Editor, reporter, civic researcher, designated reviewer. | Confirms material links, corrects cases, approves inquiry artifacts, approves publication. | Delegate public claims or outreach without reviewing the underlying evidence. |

## 3. Agent Topology

```text
Source event
    ↓
Deterministic Orchestrator
    ├─ Source Sentinel / Artifact Vault
    ├─ Document Evidence Agent ─┐
    ├─ Media Evidence Agent ────┤
    └─ Structured data adapter ─┘
                                  ↓
                           Schema + provenance validation
                                  ↓
                         Entity Resolution Agent
                                  ↓
                            Case Linker Agent
                                  ↓
                         Delta Investigator Agent
                                  ↓
                  Quality & Safety Reviewer Agent
                       ├─ no material delta → update/close watch
                       └─ verified delta → Inquiry Planner Agent
                                                ↓
                                         Human approval gate
                                                ↓
                                   Brief Builder / Artifact Worker
                                                ↓
                                Draft only → optional human publication
```

## 4. Orchestrator Responsibilities

The orchestrator should be implemented as a stateful application service, not as one large LLM prompt. It may call an LLM for a narrow **routing classification** if source content is ambiguous, but every transition must be validated by code.

| Responsibility | Required behavior |
|---|---|
| **Event intake** | Accept only allowlisted source adapters and schema-valid `SourceEvent` objects. Compute/verify a source fingerprint. |
| **Idempotency** | Create a stable job key from the source version, artifact hash, job type, agent version, and case scope. A duplicate delivery must not produce duplicate evidence or action artifacts. |
| **Work routing** | Select the smallest permitted set of agents based on MIME type, source type, case state, and event class. |
| **Evidence bounds** | Pass agents only relevant source artifacts, previous verified case state, and explicit retrieval references. Never allow open-ended web search during case construction unless a separate approved source adapter created a new event. |
| **Validation** | Validate every agent response against a typed schema, source-anchor rules, privacy rules, and policy checks before it affects case state. |
| **State persistence** | Append valid evidence/case events to a ledger; update materialized case state only through deterministic services. |
| **Approval enforcement** | Require a signed, expiring, case-bound approval token before an inquiry packet is finalized for external use or a brief is sent to any destination. |
| **Recovery** | Retry transient jobs; send terminal failures to a dead-letter queue; retain enough context for safe replay. |
| **Observability** | Emit trace IDs, job lineage, source references, agent/version IDs, validation outcomes, cost usage, and approval events. |

## 5. Authority Matrix

| Agent / service | Read | Write | May create claims? | May perform external side effect? |
|---|---|---|---:|---:|
| **Source Sentinel** | Allowlisted source metadata and public source response | Raw artifact metadata only, through vault service | No | Retrieves permitted public content only |
| **Document Evidence Agent** | One bounded document/artifact plus extraction schema | Draft typed evidence response only | Extracted, cited facts only | No |
| **Media Evidence Agent** | Public recording metadata, diarized transcript, approved clip context | Draft timestamped evidence response only | Extracted, cited facts only | No |
| **Entity Resolution Agent** | Candidate evidence, known public entities, user corrections | Candidate/confirmed link proposal only | No independent claims | No |
| **Case Linker** | Verified evidence and active case state | Case-link proposal only | No | No |
| **Delta Investigator** | Original commitment and bounded later evidence | Decision Delta proposal only | Only a cited comparison | No |
| **Quality & Safety Reviewer** | Proposed Delta/brief plus source map | Validation decision and required fixes | No | No |
| **Inquiry Planner** | Verified uncertainty/gap and relevant sources | Inquiry proposal only | No | No |
| **Brief Builder** | Verified meeting facts/case updates and editorial template | Draft artifact only | Only sourced statements | No |
| **Approval Service** | Request, case, artifact hash, human identity/role | Approval event/token | No | Enables a limited downstream worker only |
| **Artifact/Publication Worker** | Valid approval token and frozen draft | Generated packet or destination draft | No new claims | Only exact approved action; publication remains explicit human approval |

## 6. Global Policy Contract

Every AI agent receives the following policy contract in addition to its role-specific system prompt:

```text
You are a component of CivicTrace, a public-interest evidence system.

NON-NEGOTIABLE RULES
1. Work only from the source artifacts, structured case state, and tool results supplied in this task. Do not browse, guess, or rely on outside facts.
2. Preserve provenance. Every factual output must reference one or more supplied evidence IDs and precise anchors. If no sufficient evidence exists, output UNKNOWN or REQUEST_NEEDED.
3. Do not allege corruption, fraud, misconduct, illegality, motive, or causation. Describe only what the supplied record supports, conflicts with, or does not establish.
4. Do not infer private or sensitive personal information. Do not process individual student records, attendance, grades, discipline, disability, health, family, address, or other personally identifying information.
5. Do not identify a person from a diarization label or voice. A speaker label is not a name. Attribute a speaker only when supplied evidence explicitly supports the attribution.
6. Do not create, send, publish, file, contact, or authorize any external communication. You may propose a draft only when your role permits it.
7. Return only schema-valid structured output. Do not add fields, citations, sources, or certainty not supplied in the task.
8. If records conflict, preserve the conflict. If a record is absent, preserve the absence. Never smooth uncertainty into a plausible narrative.
9. Use neutral, non-advocacy language. State material facts, uncertainty, and next evidence needed.
10. A human reviewer has final authority over material links, inquiries, and any external-facing artifact.
```

## 7. Shared Structured Output Rules

All agents must return JSON that validates against a versioned schema. Text shown to users is rendered from validated fields rather than copied directly from a model response. At minimum, every factual object must contain:

```json
{
  "object_type": "Evidence | Commitment | Decision | ActionItem | CandidateLink | DecisionDelta | Inquiry | BriefSection",
  "text": "A concise neutral statement",
  "evidence_ids": ["ev_123"],
  "anchors": [
    {
      "artifact_id": "art_456",
      "anchor_type": "page | table_cell | transcript_time | video_time | dataset_row | map_feature",
      "anchor_value": "p. 12 | 01:12:08-01:12:31 | row:abc"
    }
  ],
  "status": "SUPPORTED | CANDIDATE_LINK | CONFLICTING | UNKNOWN | NOT_PUBLISHED | REQUEST_NEEDED | HUMAN_REVIEW",
  "confidence": 0.0,
  "limitations": ["What this object does not establish"]
}
```

The application—not the agent—enforces confidence ranges, minimum source-anchor count, case permissions, and any transition from candidate to confirmed evidence.


---

## 8. Agent Catalog at a Glance

| ID | Agent | Primary purpose | Invocation | Model recommendation | Output |
|---|---|---|---|---|---|
| **A0** | Orchestration Classifier | Selects the permitted workflow route for a validated event. | Every source event or human correction. | Gemini 3.5 Flash only if deterministic routing is insufficient. | `RoutePlan` |
| **A1** | Source Sentinel | Normalizes allowed public source changes and preserves artifacts. | Scheduled/push source discovery. | Deterministic adapter; no model by default. | `SourceEvent`, `Artifact` |
| **A2** | Document Evidence Agent | Extracts citations, commitments, votes, dates, actions, and limits from documents/tables. | New PDF/HTML/CSV/image artifact. | Gemini 3.5 Flash multimodal. | `Evidence[]`, `Decision[]`, `Commitment[]` |
| **A3** | Media Evidence Agent | Uses diarized/transcribed public meeting media to create timestamped meeting facts. | Completed transcript/media artifact. | Gemini 3.5 Flash + Speech-to-Text output. | `SpeakerSegment[]`, `MeetingFact[]` |
| **A4** | Entity Resolution Agent | Links evidence to public entities, projects, places, vendors, schools, and cases. | New verified evidence or user correction. | Gemini 3.5 Flash plus deterministic similarity/retrieval. | `EntityLink[]` |
| **A5** | Case Linker Agent | Determines whether verified evidence belongs in an existing case or should create a candidate case. | Valid evidence/entity links. | Gemini 3.5 Flash. | `CaseLinkProposal` |
| **A6** | Delta Investigator | Compares prior public commitments against later evidence. | Case update with relevant new evidence. | Gemini 3.5 Flash. | `DecisionDelta` or `NoMaterialDelta` |
| **A7** | Quality & Safety Reviewer | Rejects unsupported, unsafe, overbroad, privacy-risky, or politically loaded outputs. | Before any case delta, inquiry, or brief becomes user-visible. | Gemini 3.5 Flash with deterministic policy checks. | `ReviewDecision` |
| **A8** | Inquiry Planner | Proposes the narrowest next public-record question or source to resolve a defined gap. | Approved Decision Delta / unresolved case. | Gemini 3.5 Flash. | `InquiryProposal` |
| **A9** | Brief Builder | Builds a concise, source-grounded meeting/case brief from validated objects. | Reviewer requests brief or monitored meeting completes. | Gemini 3.5 Flash. | `BriefDraft` |

The Source Sentinel and Approval/Artifact workers are intentionally more deterministic than agentic. This protects the system from the common anti-pattern of giving an LLM browser, database, email, and publishing power under one broad instruction.

---

## 9. A0 — Orchestration Classifier

### Purpose

The Orchestration Classifier decides which permitted processing route applies to an already validated event. It is optional: common routes should be deterministic from artifact type and source adapter. Use it only where a source package can plausibly contain multiple valid processing paths, such as a meeting bundle that includes an agenda PDF, a recording, a final minute document, and a related data attachment.

### Inputs

- Validated `SourceEvent` metadata.
- Artifact manifest only: MIME types, hashes, source adapter, jurisdiction, event type, and availability state.
- Active case IDs and high-level status only; no unbounded corpus access.

### Allowed tools

- Read-only route registry.
- Read-only artifact manifest.
- No browser, external search, database mutation, email, publishing, or approval tools.

### Output contract

```json
{
  "route": "DOCUMENT_ONLY | MEDIA_ONLY | DOCUMENT_AND_MEDIA | STRUCTURED_DATA | NO_ACTION | HUMAN_REVIEW",
  "agent_sequence": ["A2", "A4", "A5", "A6", "A7"],
  "reason_codes": ["meeting_agenda_pdf", "recording_available"],
  "blocked_reason": null,
  "required_artifact_ids": ["art_001", "art_002"]
}
```

### System prompt

```text
You are the CivicTrace Orchestration Classifier.

Your job is to select the smallest permitted processing route for a VALIDATED public-source event. You do not analyze civic substance, create evidence, or decide what is true. You only route work.

Use only the supplied event metadata, artifact manifest, route registry, and active-case metadata. Never assume an artifact exists or is readable if it is not listed as available.

ROUTING RULES
- Prefer deterministic routes. Return HUMAN_REVIEW when the source package cannot be classified safely.
- Select only agents that are necessary for the available artifact types.
- An image/PDF/document requires A2. A completed transcript or public recording requires A3. Structured data requires the structured-data adapter and may later invoke A4/A5.
- Do not route an event to A6 unless there is a verified or candidate case link route available.
- Do not route directly to A8 or A9. They run only after validation and, where required, human review.
- If expected material is unavailable, choose NO_ACTION or HUMAN_REVIEW with a precise reason code; do not attempt recovery by inventing data.

Return only a RoutePlan JSON object that conforms exactly to the supplied schema.
```

---

## 10. A1 — Source Sentinel

### Purpose

The Source Sentinel is a source-adapter service that watches approved public sources and turns a detected change into an immutable, replayable event. It should be code-first and model-free. A narrow model call is permissible only to classify an already downloaded artifact’s format when deterministic detection fails, and the result must never replace the original artifact metadata.

### Inputs

- Source adapter configuration: canonical source URL/API, refresh cadence, jurisdiction, allowlisted path/domain, and terms/rate-limit note.
- Previous source fingerprint and last successful cursor.

### Outputs

- `SourceEvent` with external ID, canonical URL, fingerprint, retrieval timestamp, event type, and artifact manifest.
- `Artifact` metadata for stored public source material.
- Explicit `NOT_PUBLISHED` / `SOURCE_UNAVAILABLE` event where relevant.

### System prompt for optional format classification

```text
You are the CivicTrace Source Sentinel Format Classifier.

Classify the supplied artifact metadata and first bytes/text only to determine its technical handling route. Do not extract civic facts, interpret content, invent a source, or modify source metadata.

Choose one of: PDF, IMAGE, HTML, JSON, CSV, AUDIO, VIDEO, TRANSCRIPT, ARCHIVE, UNKNOWN.

If the artifact is inaccessible, incomplete, corrupted, blocked, or absent, return UNKNOWN with the appropriate availability reason. Never treat a missing artifact as a blank document or infer its contents.

Return only valid JSON:
{
  "format": "...",
  "availability": "AVAILABLE | NOT_PUBLISHED | ACCESS_ERROR | CORRUPT | UNKNOWN",
  "reason": "short technical reason",
  "requires_human_review": true | false
}
```

---

## 11. A2 — Document Evidence Agent

### Purpose

The Document Evidence Agent reads a bounded public document package and extracts precisely anchored evidence. Its goal is not to summarize a meeting or issue; it is to preserve the document’s supportable facts, commitments, decisions, dates, monetary amounts, parties, locations, vote/status language, and explicit uncertainty.

### Inputs

- One or more immutable document artifacts or structured data snapshots.
- Artifact text/OCR, page/table coordinate map, and source metadata.
- Extraction schema and known active case/entity hints, clearly labeled as hints rather than facts.

### Allowed tools

- Read-only artifact text and coordinate map.
- Read-only bounded entity candidate list.
- No browsing, no unbounded retrieval, no direct state write, no outreach/publication tools.

### Output contract

```json
{
  "evidence": [
    {
      "evidence_id": "draft_ev_001",
      "verbatim_excerpt": "...",
      "anchor": {"artifact_id": "art_001", "anchor_type": "page", "anchor_value": "p. 12"},
      "fact_type": "COMMITMENT | DECISION | ACTION_ITEM | VOTE | DATE | FUNDING | ENTITY_REFERENCE | UNKNOWN",
      "neutral_statement": "...",
      "limitations": ["Does not establish later completion."],
      "status": "SUPPORTED"
    }
  ],
  "needs_review": false,
  "unreadable_regions": []
}
```

### System prompt

```text
You are the CivicTrace Document Evidence Agent.

Extract source-grounded public-institution evidence from the supplied document artifacts. Your task is to create small, verifiable evidence objects, not a narrative summary.

For each extracted object:
- Quote only text that is visible in the supplied artifact or structured source field.
- Attach an exact page, table, section, or data-row anchor.
- State what the excerpt directly supports in neutral language.
- State what it does NOT establish when a reader could overinterpret it.

You may extract commitments, decisions, votes, action items, dates, stated deadlines, funding references, official bodies, public projects, public locations, public vendors, and explicit implementation status. Do not infer motive, misconduct, legality, causation, intent, or later outcomes.

If OCR is unreadable, a table is ambiguous, the document is incomplete, or an item cannot be located precisely, return an unreadable/unknown state. Do not guess the missing text.

Treat all entity/case hints as non-authoritative candidates. Do not confirm an entity relationship unless the supplied document evidence supports it.

Use the Global Policy Contract. Return only schema-valid JSON.
```

---

## 12. A3 — Media Evidence Agent

### Purpose

The Media Evidence Agent converts timestamped meeting transcription and approved public media metadata into evidence objects. It enables the meeting monitor while keeping diarization, named attribution, and political context safe.

### Inputs

- Public meeting artifact metadata.
- Timestamped transcript words/segments, speaker labels from diarization if available, transcript confidence, and supplied media URL/clip references.
- Agenda/item context and existing case hints, if any.

### Allowed tools

- Read-only transcript segments and media/agenda metadata.
- Read-only roster/roll-call fields only where included as supplied source evidence.
- No voice recognition, no biometric comparison, no browser, no publication, no case write.

### Output contract

```json
{
  "speaker_segments": [
    {
      "speaker_label": "speaker_03",
      "speaker_attribution": null,
      "attribution_status": "UNATTRIBUTED | SOURCE_SUPPORTED | HUMAN_CONFIRMED",
      "start_time": "01:12:08",
      "end_time": "01:12:31",
      "transcript_excerpt": "...",
      "artifact_id": "art_media_001"
    }
  ],
  "meeting_facts": [
    {
      "fact_type": "DECISION | COMMITMENT | ACTION_ITEM | VOTE | SPEAKER_CLAIM | OPEN_QUESTION",
      "neutral_statement": "...",
      "evidence_ids": ["draft_ev_101"],
      "status": "SUPPORTED",
      "limitations": ["The excerpt does not establish that the action was later completed."]
    }
  ],
  "media_quality_flags": ["CROSSTALK | LOW_CONFIDENCE | MISSING_ROSTER"]
}
```

### System prompt

```text
You are the CivicTrace Media Evidence Agent.

Analyze only the supplied public meeting transcript, diarization labels, media metadata, agenda context, and explicitly supplied roster/roll-call evidence. Produce timestamped, source-grounded meeting facts.

A diarization label such as speaker_03 is NOT a person’s name. Never identify a speaker from vocal characteristics or infer identity from role, topic, or likely attendance. Attribute a name or official role only when the supplied evidence explicitly supports it; otherwise keep speaker_attribution null.

Extract only what the transcript and linked meeting material establish: decisions, motions, votes, action items, stated commitments, amendments, public questions, and clearly marked claims by a source-supported speaker. Distinguish a claim made in discussion from a final Board/Council decision.

Handle crosstalk, poor audio, low-confidence transcription, unclear votes, and incomplete recordings by raising a quality flag or UNKNOWN state. Never reconstruct speech that is not present.

Do not infer political intent, wrongdoing, causation, or future completion. Do not publish a meeting brief. Return only schema-valid JSON under the Global Policy Contract.
```

---

## 13. A4 — Entity Resolution Agent

### Purpose

The Entity Resolution Agent connects public-source evidence to a canonical public body, project, place, vendor, school, or existing case. It is deliberately conservative: false links are more harmful than unresolved links.

### Inputs

- Validated evidence objects.
- Candidate entity list from deterministic search across known public entities and aliases.
- Normalized location/address/project/vendor fields.
- Reviewer corrections attached to the case/entity.

### Allowed tools

- Read-only candidate index and case-specific correction store.
- No web search, no modification of canonical entity table, no direct case state mutation.

### Output contract

```json
{
  "links": [
    {
      "evidence_id": "ev_001",
      "entity_id": "entity_123",
      "link_type": "REFERS_TO | LOCATED_AT | FUNDED_BY | OWNED_BY | IMPLEMENTS",
      "match_status": "CONFIRMED | CANDIDATE | REJECTED",
      "supporting_evidence_ids": ["ev_001"],
      "rationale": "Exact project number and address match.",
      "limitations": []
    }
  ],
  "requires_human_review": false
}
```

### System prompt

```text
You are the CivicTrace Entity Resolution Agent.

Determine whether supplied evidence refers to one of the supplied candidate public entities, projects, places, vendors, schools, or cases. You are a conservative matching system, not a researcher.

Confirm a link only when the supplied evidence contains a strong, explicit match such as an exact project identifier, official file number, address/parcel, vendor name plus contract reference, official body name, or a reviewer-confirmed correction. If names are similar but not uniquely supported, emit CANDIDATE. If evidence contradicts the candidate, emit REJECTED.

Never use outside knowledge, internet search, voice identity, demographic assumptions, or political context to resolve identity. Never convert a candidate match into a fact merely because it seems likely.

Respect human corrections as high-priority constraints for this case. Return only schema-valid JSON under the Global Policy Contract.
```


---

## 14. A5 — Case Linker Agent

### Purpose

The Case Linker determines whether a verified evidence object should update an existing Promise Ledger case, create a candidate case, or remain unlinked. It distinguishes **relevance** from **proof**: a document may discuss the same topic without changing the same public commitment.

### Inputs

- Validated evidence objects and entity link proposals.
- Active case summaries: original commitment, named entities/places, expected evidence, timeline, and current uncertainty state.
- Reviewer corrections and topic-watch configuration.

### Allowed tools

- Read-only case summaries and evidence graph neighborhood.
- No case creation/update call; it returns a proposal that the deterministic graph service validates.

### Output contract

```json
{
  "proposal_type": "LINK_EXISTING | CREATE_CANDIDATE_CASE | NO_LINK | HUMAN_REVIEW",
  "case_id": "case_001",
  "linked_evidence_ids": ["ev_001"],
  "relationship": "UPDATES_COMMITMENT | EXPECTED_EVIDENCE | CONTEXT_ONLY | CONTRADICTS | RELATED_TOPIC",
  "support": ["Exact file number matches original commitment."],
  "limitations": ["Does not establish project completion."],
  "materiality_hint": "LOW | MEDIUM | HIGH"
}
```

### System prompt

```text
You are the CivicTrace Case Linker Agent.

Using only validated evidence, resolved/candidate entity links, active case summaries, and reviewer corrections, propose whether evidence belongs to an existing Promise Ledger case.

A case link must be based on an explicit shared identifier, public body, project/place, official file number, vendor/contract reference, stated milestone, or other source-supported connection. Topic similarity alone is not sufficient for a material case update.

Classify the relationship precisely. CONTEXT_ONLY means the source is relevant but does not change the commitment. EXPECTED_EVIDENCE means it is a record the case was waiting for. CONTRADICTS means the source text conflicts with prior source-backed case state; it does not mean the source proves wrongdoing.

When multiple cases are plausible or the relationship could materially affect a public conclusion, return HUMAN_REVIEW. Do not create or mutate case state yourself. Return only schema-valid JSON under the Global Policy Contract.
```

---

## 15. A6 — Delta Investigator Agent

### Purpose

The Delta Investigator performs CivicTrace’s central reasoning task: comparing an original public commitment with later public evidence to determine whether the record shows a supported update, a conflict, an unresolved gap, or no material change. It must always be evidence-first and never equate delay, missing data, or inconsistency with misconduct.

### Inputs

- Frozen active case state, including original `Commitment` objects and expected evidence.
- Newly validated case-linked evidence.
- Relevant timeline entries and unresolved-gap states.
- Case-specific reviewer corrections.

### Allowed tools

- Read-only case evidence bundle and temporal ordering tool.
- No external search, no broad corpus search, no direct write, no inquiry/publication tool.

### Output contract

```json
{
  "result_type": "DECISION_DELTA | NO_MATERIAL_DELTA | HUMAN_REVIEW",
  "case_id": "case_001",
  "delta_category": "ADVANCED | REVISED | DEFERRED | CONFLICTING | EXPECTED_EVIDENCE_ARRIVED | RECORD_GAP | OTHER",
  "neutral_summary": "The later record revises the stated target date from X to Y.",
  "original_evidence_ids": ["ev_commitment_001"],
  "later_evidence_ids": ["ev_later_002"],
  "what_is_established": ["..."],
  "what_is_not_established": ["..."],
  "next_evidence_needed": "...",
  "materiality": "LOW | MEDIUM | HIGH",
  "confidence": 0.0,
  "limitations": ["..."],
  "requires_human_review": true
}
```

### System prompt

```text
You are the CivicTrace Delta Investigator.

Compare a frozen public commitment with later, supplied public evidence. Your task is to identify a source-grounded change, conflict, expected-evidence arrival, or record gap. You are not a prosecutor, auditor, or commentator.

A Decision Delta requires BOTH:
1. at least one precise anchor for the original commitment; and
2. at least one precise anchor for later evidence.

State only the narrowest comparison the evidence supports. Examples: a later document gives a different target date; a meeting record says an item was deferred; an expected report was published; the record supplied does not establish whether a stated milestone occurred.

Do not infer corruption, fraud, negligence, legality, motive, causation, intent, project failure, or outcome from a delay, missing record, conflicting statement, or budget line. Do not equate discussion with a final decision. Do not equate a speaker claim with institutional fact.

If evidence is insufficient, return NO_MATERIAL_DELTA or HUMAN_REVIEW. Preserve conflicts and unknowns explicitly. Propose the next evidence needed only when it would directly resolve a defined gap.

Return only schema-valid JSON under the Global Policy Contract.
```

---

## 16. A7 — Quality & Safety Reviewer

### Purpose

The Quality & Safety Reviewer is a second-pass specialist. It checks a proposed Decision Delta, Inquiry Proposal, or Brief Draft against source-grounding, neutral-language, privacy, policy, and scope rules. It does not rewrite history or create new facts; it approves, rejects, or requests precise corrections.

A deterministic policy service runs alongside it. The model reviewer does not replace hard checks such as required source IDs, valid approval token, PII allowlist/denylist, or schema validation.

### Inputs

- Proposed structured output.
- Source map containing artifact IDs, excerpts, anchors, and access state.
- Global policy contract and case/jurisdiction policy.
- Deterministic check results.

### Allowed tools

- Read-only proposal, source map, policies, and validation report.
- No source discovery, no web search, no state change, no external action.

### Output contract

```json
{
  "decision": "APPROVE | REJECT | REVISE | HUMAN_REVIEW",
  "blocking_issues": [
    {"code": "MISSING_LATER_ANCHOR", "field": "later_evidence_ids", "fix": "Provide one later evidence anchor or downgrade to NO_MATERIAL_DELTA."}
  ],
  "non_blocking_notes": [],
  "approved_claim_ids": ["claim_001"],
  "policy_flags": ["NO_PII_DETECTED"],
  "review_summary": "..."
}
```

### System prompt

```text
You are the CivicTrace Quality & Safety Reviewer.

Review a proposed Decision Delta, inquiry, or brief for evidence integrity and policy compliance. You are not allowed to introduce new facts or replace missing evidence with a more plausible interpretation.

Reject or request revision when any material claim lacks a precise source anchor, when an original/later comparison lacks both sides, when a speaker is named without source-supported attribution, when language implies wrongdoing/motive/causation beyond the supplied record, when privacy rules may be violated, or when the draft proposes an unapproved external action.

Approve only content that is neutral, scope-bounded, source-grounded, and clearly labels uncertainty. Preserve a conflict or missing record as a visible condition, not as proof of a negative conclusion.

Your response must identify specific blocking fields and fixes. Return only schema-valid JSON under the Global Policy Contract.
```

---

## 17. A8 — Inquiry Planner

### Purpose

The Inquiry Planner turns a defined, evidence-supported gap into the narrowest useful next question. It creates a draft research packet request; it never sends an email, files a public-records request, contacts an official, or makes a legal judgment.

### Inputs

- Quality-approved Decision Delta or unresolved case state.
- Exact `next_evidence_needed` field and relevant citations.
- Approved inquiry templates/rules for the jurisdiction and user organization.

### Allowed tools

- Read-only case evidence, source catalog, and inquiry templates.
- No email, form submission, browser navigation, publication, or request-filing tool.

### Output contract

```json
{
  "inquiry_type": "SOURCE_QUESTION | RECORDS_REQUEST_OUTLINE | WATCH_REMINDER | HUMAN_RESEARCH_TASK",
  "proposed_question": "...",
  "scope_rationale": "...",
  "target_record_or_source": "...",
  "supporting_evidence_ids": ["ev_001", "ev_002"],
  "excluded_requests": ["No personnel or student-level information."],
  "approval_required": true,
  "limitations": ["This request does not assert that the milestone was missed."]
}
```

### System prompt

```text
You are the CivicTrace Inquiry Planner.

Create the narrowest possible next research action that would resolve a specific, quality-approved evidence gap. The action must be proportionate to the gap and tied to cited public evidence.

You may propose: a focused question for an official/public body, a records-request outline, a source to watch next, or a human research task. Do not write an accusatory question, make a legal claim, request private/student-level data, request broad fishing-expedition records, contact anyone, or file anything.

State what the current record establishes, what it does not establish, why the requested record/question is relevant, and what is expressly outside scope. If the case lacks enough evidence to define a narrow next step, return HUMAN_REVIEW.

Return only schema-valid JSON under the Global Policy Contract.
```

---

## 18. A9 — Brief Builder

### Purpose

The Brief Builder creates a concise draft meeting brief or case update from **validated facts only**. It is the presentation agent, not the system of record. The draft is never published automatically.

### Inputs

- Quality-approved meeting facts, Decision Deltas, case updates, action items, and source anchors.
- Organization-approved brief template, target audience, and neutral style guide.
- Approved speaker attribution fields only.

### Allowed tools

- Read-only validated case state and style template.
- No fresh retrieval, no claim creation, no state mutation, no publication tool.

### Output contract

```json
{
  "title": "...",
  "what_changed": [{"text": "...", "evidence_ids": ["ev_001"]}],
  "promise_ledger_updates": [{"case_id": "case_001", "text": "...", "evidence_ids": ["ev_002"]}],
  "action_items": [{"text": "...", "evidence_ids": ["ev_003"]}],
  "evidence_clips": [{"label": "...", "artifact_id": "art_001", "anchor": "01:12:08-01:12:31"}],
  "watch_next": [{"text": "...", "reason": "..."}],
  "uncertainty_notice": "...",
  "status": "DRAFT_REQUIRES_HUMAN_APPROVAL"
}
```

### System prompt

```text
You are the CivicTrace Brief Builder.

Create a concise, neutral public-interest meeting brief from ONLY the quality-approved facts and case updates supplied. Your output must follow five sections: What Changed, Promise Ledger Updates, Action Items, Evidence Clips, and Watch Next.

Every sentence that asserts a fact must carry its supplied evidence ID. Include an uncertainty notice whenever the record is incomplete, conflicting, or pending. Use source-supported speaker names/roles only; otherwise use a neutral label such as “a meeting participant” or “Speaker 3.”

Do not add context from outside the supplied evidence, infer motive/causation/wrongdoing, convert discussion into a decision, or say that an action is complete without a cited record. Do not publish, address readers with advocacy language, or claim that this draft is final.

Set status to DRAFT_REQUIRES_HUMAN_APPROVAL. Return only schema-valid JSON under the Global Policy Contract.
```

---

## 19. Recommended Agent Invocation Sequences

| Workflow | Sequence | Human gate |
|---|---|---|
| **New City agenda/document** | A1 → A0 → A2 → validator → A4 → A5 → A6 → A7 | Required before A8/A9 is made user-actionable. |
| **New meeting recording** | A1 → A0 → Speech-to-Text batch → A3 → validator → A4 → A5 → A6 → A7 → A9 | Required before brief publication or inquiry artifact use. |
| **New structured data row / update** | A1 → structured-data validator → A4 → A5 → A6 → A7 | Required before inquiry packet. |
| **Reviewer corrects entity/case link** | correction event → A4 → deterministic case update → A6 if material → A7 | Reviewer already supplied correction; any new inquiry still needs approval. |
| **MPS public Board/plan update** | A1 MPS adapter → A0 → A2/A3 → validator + institutional-data policy check → A4 → A5 → A6 → A7 → A9 | Required before publication. Student-data policy blocks unsuitable inputs. |


---

## 20. Orchestration State Machine

### 20.1 Source-event lifecycle

| State | Owner | Entry condition | Exit condition | Terminal? |
|---|---|---|---|---:|
| `RECEIVED` | Orchestrator | Allowlisted adapter emits schema-valid event. | Fingerprint/idempotency check completes. | No |
| `DUPLICATE_SUPPRESSED` | Orchestrator | Matching terminal idempotency key exists. | Audit event appended. | Yes |
| `ARTIFACT_PENDING` | Source Sentinel | Event is new and source artifact must be retrieved/preserved. | Artifact stored or availability failure recorded. | No |
| `NOT_PUBLISHED` | Source Sentinel | Expected record/attachment has no accessible public artifact. | Reviewer/next watcher may reopen on new source event. | Conditionally |
| `ROUTED` | Orchestrator | Artifact manifest passes classification. | Agent tasks queued. | No |
| `EXTRACTING` | Document/Media Agent | Relevant task is running. | Valid output, retryable failure, or terminal failure. | No |
| `VALIDATION_FAILED` | Deterministic validator | Schema, anchor, policy, or PII check fails. | Correctable retry/review or dead-letter. | No |
| `LINKING` | Entity/Case Agents | Valid evidence exists. | Candidate/confirmed/no-link proposal is validated. | No |
| `INVESTIGATING` | Delta Investigator | Case-linked evidence may affect an active case. | Delta/no-delta/review result validated. | No |
| `HUMAN_REVIEW` | Reviewer | Materiality, evidence, identity, or policy cannot be resolved safely. | Reviewer correction, approval, deferral, or closure. | No |
| `INQUIRY_STAGED` | Inquiry Planner | Quality-approved, bounded evidence gap exists. | Human approval/rejection. | No |
| `ARTIFACT_RENDERED` | Artifact Worker | Valid approval token exists. | Draft packet/brief stored and audited. | No |
| `COMPLETED` | Orchestrator | All expected workflow outputs succeed or are correctly deferred. | Audit record final. | Yes |
| `DEAD_LETTER` | Recovery Service | Retry budget exhausted or unrecoverable system error. | Admin/reviewer triggers controlled replay. | Conditionally |

### 20.2 Deterministic transition rules

```text
IF source_fingerprint AND agent_version AND job_type AND case_scope equal an existing terminal job
  THEN set DUPLICATE_SUPPRESSED; do not call an agent.

IF raw artifact is not stored or represented as an explicit unavailability state
  THEN no evidence-extraction agent may start.

IF an agent output fails schema, source-anchor, or privacy validation
  THEN it must not update case state; create VALIDATION_FAILED and attach an actionable error.

IF a Delta lacks both original and later source anchors
  THEN downgrade to NO_MATERIAL_DELTA or HUMAN_REVIEW; never render it as a Decision Delta.

IF proposed action includes publish, send, file, contact, or any destination outside the internal workspace
  THEN require a valid, case-bound approval token and destination allowlist.

IF source/event record is MPS-scoped and data classification is not PUBLIC_INSTITUTIONAL
  THEN block processing and raise POLICY_BLOCKED.
```

## 21. Validation Gates

| Gate | Applied after | Deterministic checks | Agent-assisted checks | On failure |
|---|---|---|---|---|
| **G1 — Source admission** | Source Sentinel | Domain/source allowlist, MIME/size policy, hash, terms note, public access scope. | Optional technical format classification. | Reject or mark unavailable; no artifact parsing. |
| **G2 — Artifact integrity** | Artifact vault | Storage URI, content hash, retrieval timestamp, corruption scan. | None. | Retry/download or `SOURCE_UNAVAILABLE`. |
| **G3 — Extraction contract** | A2/A3 | Schema validation, anchor existence, artifact ownership, field limits. | Quality check for quote/anchor fit. | Return to extraction/review; do not persist evidence. |
| **G4 — Privacy / data eligibility** | Before all civic reasoning | Jurisdiction allowlist, MPS institutional-only policy, PII detection/redaction rule. | Safety Reviewer flagging of indirect privacy risk. | Block event and retain audit record only. |
| **G5 — Entity link** | A4/A5 | Candidate IDs exist; no rejected/human-corrected link reintroduced. | Conservative relation sufficiency review. | Keep candidate/unlinked; route material ambiguity to reviewer. |
| **G6 — Delta grounding** | A6 | Original/later anchor count, temporal ordering, case association, required fields. | Neutrality and evidence-sufficiency review. | No-delta or human review. |
| **G7 — Draft quality** | A8/A9 | All assertions carry approved evidence IDs; no unauthorized destination. | Neutral language, uncertainty, non-defamation review. | Reject/revise; preserve source case. |
| **G8 — Action authorization** | Approval/Artifact Worker | Signature, user role, case ID, artifact hash, expiry, destination allowlist. | None. | Hard block; audit event. |

## 22. Approval Model

### 22.1 Approval is a signed action capability

An approval is not a general “yes” to the agent. It is a short-lived permission for one frozen artifact and one specific action. The approval service creates a signed token only after the reviewer sees the source-backed draft.

```json
{
  "approval_id": "apr_001",
  "case_id": "case_014",
  "artifact_hash": "sha256:...",
  "action_type": "RENDER_INQUIRY_PACKET | CREATE_CMS_DRAFT | PREPARE_RECORDS_REQUEST_OUTLINE",
  "destination_id": "internal_workspace | configured_cms_draft",
  "approved_by": "user_123",
  "approved_at": "2026-08-18T...Z",
  "expires_at": "2026-08-18T...Z",
  "scope": "exact artifact version only"
}
```

### 22.2 Actions that always require approval

| Action | Required approver | Notes |
|---|---|---|
| Render inquiry packet intended for external review | Reporter/editor/researcher with case permission | Allows a packet to be created; does not send it. |
| Create CMS/newsletter/social destination draft | Editor role | Draft-only destination. |
| Generate records-request outline | Authorized researcher/editor | Must exclude private/student-level data by policy. |
| Send an email or submit an external form | Explicit current-session user confirmation | Keep out of hackathon MVP unless required and separately demonstrated. |
| Publish public content | Editor role plus explicit final confirmation | Never automated. |

## 23. Failure Handling and Recovery

| Failure mode | Detection | System behavior | User-visible outcome |
|---|---|---|---|
| Source unavailable or attachment missing | Adapter status / HTTP / manifest. | Store source metadata; set `NOT_PUBLISHED`; schedule a future check if appropriate. | “The expected attachment is not publicly available yet.” |
| OCR/parsing failure | Parser error or low quality. | Preserve raw artifact; retry with approved fallback; otherwise route to review. | “This record needs human review; the original is preserved.” |
| Transcription low confidence/crosstalk | Speech-to-Text metadata + A3 flag. | Preserve timestamped transcript; do not create confident speaker attribution; route critical facts to review. | “Audio quality prevents a reliable conclusion.” |
| Duplicate event delivery | Idempotency-key lookup. | Suppress duplicate downstream job; append audit event. | No duplicate case update. |
| Model timeout/transient error | Task exception/time budget. | Retry within defined limit with same idempotency key; trace attempts. | Processing status shows retry. |
| Model schema/grounding failure | Validator. | Reject output; re-run limited task or send to review. | No unsupported assertion appears. |
| Entity ambiguity | Low-confidence/multiple candidate links. | Retain as `CANDIDATE_LINK`; do not trigger material Delta without reviewer. | User can confirm/reject candidate link. |
| Conflicting public records | A6/A7 review. | Preserve both sources as `CONFLICTING`; suggest narrow next evidence. | “Public record conflict requires review.” |
| Policy/private-data violation | Eligibility classifier/policy engine. | Block processing; quarantine/restrict artifact metadata; notify authorized operator. | No private content appears in the app. |
| Approval token expired/invalid | Approval Service. | Hard-block Artifact Worker. | “Approval required or expired.” |

## 24. Orchestrator Pseudocode

```python
async def handle_source_event(event: SourceEvent) -> None:
    assert event.source_id in SOURCE_ALLOWLIST
    job_key = make_idempotency_key(event, parser_version, agent_bundle_version)

    if ledger.has_terminal_job(job_key):
        ledger.append_audit(event.id, "DUPLICATE_SUPPRESSED")
        return

    job = ledger.create_job(job_key, state="RECEIVED")
    artifact = await vault.preserve_or_record_unavailability(event)

    if artifact.status != "AVAILABLE":
        ledger.append_case_signal(event, status="NOT_PUBLISHED")
        ledger.finish(job, "COMPLETED")
        return

    route = await route_event_deterministically_or_with_A0(event, artifact)
    assert policy.is_allowed(artifact, route)

    evidence = await run_extractors(route, artifact)
    valid_evidence = validators.validate_evidence(evidence, artifact)
    if not valid_evidence:
        ledger.fail(job, "VALIDATION_FAILED")
        return

    links = await A4.resolve(valid_evidence, candidate_entities, corrections)
    case_proposal = await A5.link(valid_evidence, links, active_cases)
    case_state = graph_service.apply_validated_links(case_proposal)

    delta = await A6.investigate(case_state, valid_evidence)
    review = await A7.review(delta, evidence_map)
    graph_service.apply_reviewed_result(review)

    if review.decision == "APPROVE" and delta.result_type == "DECISION_DELTA":
        await stage_editor_task(delta)

    ledger.finish(job, "COMPLETED")
```

The pseudocode shows the central distinction: agents propose structured work; the orchestrator and deterministic services decide whether it is persisted or permitted to proceed.

## 25. Multi-Agent Acceptance Tests

| Test ID | Scenario | Expected result |
|---|---|---|
| **MA-01** | Same public meeting event delivered twice. | One artifact/evidence/case update; second job marked `DUPLICATE_SUPPRESSED`. |
| **MA-02** | Document extractor returns a commitment without page anchor. | G3 rejects it; no ledger update. |
| **MA-03** | Media agent attempts to name `speaker_03` without roster evidence. | G7 rejects named attribution; retains unlabeled speaker segment. |
| **MA-04** | Delta Agent sees an original promise but no later official record. | Returns `NO_MATERIAL_DELTA` or `REQUEST_NEEDED`, not failure/misconduct. |
| **MA-05** | MPS-related artifact contains student-level PII. | G4 blocks task before model access; logs policy event. |
| **MA-06** | Entity Resolver has two similarly named projects. | Returns `CANDIDATE_LINK` and asks for review; no automatic merge. |
| **MA-07** | Quality Reviewer detects unsupported causal wording. | Rejects/requires revision; source facts remain intact. |
| **MA-08** | Inquiry Planner requests broad “all documents” without a defined gap. | Returns `HUMAN_REVIEW` or narrow-scoping revision. |
| **MA-09** | Artifact Worker receives expired approval token. | Hard block, no packet/destination draft created. |
| **MA-10** | User corrects a place association. | Correction is persisted and influences future A4/A5 matching for that case. |

## 26. Implementation Notes for Google ADK

In Google ADK, define each reasoning role as a specialized agent with a strict output schema and a narrow toolset. The workflow controller should remain application code triggered by Pub/Sub/Cloud Tasks, rather than relying on a free-form agent to determine persistence or permissions. Tools that mutate Firestore, create Cloud Storage artifacts, or prepare destination drafts should be exposed only to deterministic services or a worker that validates a signed approval token.

This approach still showcases multi-agent collaboration: Gemini agents pass typed evidence, links, delta proposals, and draft artifacts through durable state. It is more credible than letting one agent autonomously call every service, because the case history, retries, security posture, and human decisions remain observable and testable.

