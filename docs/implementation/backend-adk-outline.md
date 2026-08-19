# CivicTrace Python Backend and Google ADK Outline

## Purpose

This document turns the CivicTrace PRD into a practical **Python + Google ADK** implementation path. It is intentionally a code outline, not a claim that every function is production-complete. Claude Code should verify the current ADK API names against the installed version while preserving the architecture below.

> **Implementation rule:** ADK agents are pure, bounded reasoning components. Python orchestration code owns idempotency, queues, validation, Firestore writes, and all external-facing approval requirements.

---

## 1. Runtime Shape

```text
Cloud Scheduler / replay script
          ↓
Direct City source adapter
          ↓
SourceEvent + immutable Cloud Storage artifact
          ↓
Pub/Sub event + Cloud Task with idempotency key
          ↓
Internal worker endpoint on Cloud Run
          ↓
Deterministic Route Registry
          ↓
ADK Agent Runner (bounded inputs + read-only tools)
          ↓
Pydantic schema + provenance + privacy validation
          ↓
Firestore append-only ledger + staged case state
          ↓
ADK Delta Investigator + Quality Reviewer
          ↓
Human approval event
          ↓
ADK Inquiry Planner / Brief Builder → deterministic packet renderer
```

The API service handles user-visible case, evidence, correction, and approval requests. The worker service handles all background source/event work and can be invoked only through Cloud Tasks/IAM.

---

## 2. First Vertical Slice

Implement exactly this sequence before adding media, MPS, more sources, or a broad agent team.

| Step | Build | Acceptance criterion |
|---:|---|---|
| 1 | Pydantic `SourceEvent`, `Artifact`, `Evidence`, `Commitment`, `Case`, `DecisionDelta`, and `Approval` contracts. | Contracts validate a reviewed fixture source bundle. |
| 2 | Direct Milwaukee Legistar replay adapter and local fixture mode. | Produces a source event with canonical URL, external ID, hash, and retrieval time. |
| 3 | Artifact vault abstraction with local fake and GCS implementation. | Artifact is persisted before model invocation. |
| 4 | Document Evidence Agent plus source-anchor validator. | Output is typed, anchored, and rejects malformed/unanchored evidence. |
| 5 | In-memory repository plus Firestore repository. | A validated evidence object appends one ledger event. |
| 6 | Deterministic Case Link/Delta workflow with fixture case. | Produces a Decision Delta only when original + later anchors exist. |
| 7 | Quality/Safety Review plus approval gate. | Unapproved inquiry packet request fails closed. |
| 8 | Cloud Task handler and duplicate-event test. | Same idempotency key creates no duplicate ledger event. |

---

## 3. Package Dependency Direction

```text
schemas + domain
      ↑
policies + repositories + services
      ↑
tools + agents
      ↑
orchestration + workers + API routes
      ↑
main.py
```

| Layer | May import | Must not import |
|---|---|---|
| `schemas`, `domain` | Pydantic, standard library | ADK, FastAPI, Google clients |
| `policies` | schemas/domain | FastAPI endpoints, agent runners |
| `repositories`, `services` | schemas/domain/policies | FastAPI routes, UI code |
| `tools`, `agents` | schemas/domain/policies/services interfaces | Firestore write tools, email/CMS/browser automation |
| `orchestration`, `workers` | all backend layers | Frontend code |
| `api` | services/orchestration read services | direct model/queue writes that bypass workflow |

---

## 4. Core Contracts

The code should use Pydantic models with `extra="forbid"` and literal/enum states. Every material proposed fact must include an `EvidenceAnchor`. Every case transition must be validated by code.

```python
class EvidenceAnchor(BaseModel):
    artifact_id: str
    anchor_type: Literal[
        "page", "table_cell", "dataset_row", "transcript_time", "video_time", "map_feature"
    ]
    anchor_value: str

class Evidence(BaseModel):
    evidence_id: str
    artifact_id: str
    object_type: Literal["COMMITMENT", "DECISION", "ACTION_ITEM", "VOTE", "CLAIM", "UNKNOWN"]
    verbatim_excerpt: str
    neutral_statement: str
    anchors: list[EvidenceAnchor]
    status: Literal["SUPPORTED", "UNKNOWN", "CONFLICTING", "NOT_PUBLISHED", "HUMAN_REVIEW"]
    limitations: list[str]

class DecisionDelta(BaseModel):
    case_id: str
    category: Literal["ADVANCED", "REVISED", "DEFERRED", "CONFLICTING", "EXPECTED_EVIDENCE_ARRIVED", "RECORD_GAP"]
    neutral_summary: str
    original_evidence_ids: list[str]
    later_evidence_ids: list[str]
    what_is_established: list[str]
    what_is_not_established: list[str]
    next_evidence_needed: str | None
    requires_human_review: bool = True
```

The validator must reject a `DecisionDelta` with fewer than one original and one later evidence ID, anchor-less evidence, a disallowed PII pattern, unrecognized status, or externally actionable output without a valid approval token.

---

## 5. ADK Agent Runner Boundary

The exact ADK constructor/runner API can change; isolate it in `app/agents/factory.py` and a small `AgentRunner` protocol. The rest of CivicTrace passes typed input/output models, not raw prompt strings.

```python
class AgentRunner(Protocol):
    async def run_structured(
        self,
        *,
        agent_name: str,
        payload: BaseModel,
        output_model: type[T],
        trace_id: str,
    ) -> T: ...
```

The ADK implementation should configure Gemini through Vertex AI/service identity, use the global policy contract plus agent role prompt, attach only read-only bounded tools, request a strict output schema, capture an invocation trace, parse structured JSON into Pydantic, and return it to deterministic validators.

No agent receives a Firestore write tool, generic browser tool, free-form web search tool, email tool, form-submission tool, publishing tool, approval-grant tool, or arbitrary SQL/BigQuery tool.

---

## 6. Agent Specifications

| Agent | Python module | Input | Output | Invocation gate |
|---|---|---|---|---|
| Document Evidence | `agents/document_evidence.py` | One bounded artifact text/page map plus candidate hints. | `DocumentExtraction` | Artifact stored and route permits a document. |
| Media Evidence | `agents/media_evidence.py` | Timestamped public transcript/media context. | `MediaExtraction` | STT operation succeeded; P1 only. |
| Entity Resolution | `agents/entity_resolution.py` | Valid evidence + bounded candidate entities/corrections. | `EntityLinkBatch` | Evidence passed anchor validation. |
| Case Linker | `agents/case_linker.py` | Valid evidence/links + active case summaries. | `CaseLinkProposal` | Candidate cases prefiltered deterministically. |
| Delta Investigator | `agents/delta_investigator.py` | Frozen commitment + later case-linked evidence. | `DecisionDeltaProposal` | Original/later evidence bundle exists. |
| Quality Reviewer | `agents/quality_reviewer.py` | Proposed delta/brief + source map + check results. | `ReviewDecision` | Always runs before user-visible case delta. |
| Inquiry Planner | `agents/inquiry_planner.py` | Quality-approved uncertainty/gap. | `InquiryProposal` | Human review request or approved staged delta. |
| Brief Builder | `agents/brief_builder.py` | Quality-approved facts/case updates. | `BriefDraft` | Requested by reviewer or approved meeting workflow. |

---

## 7. Deterministic Orchestration Pseudocode

```python
async def process_source_event(event: SourceEvent, *, trace_id: str) -> ProcessResult:
    policy.assert_source_allowed(event)
    job_key = idempotency.build(event, job_type="PROCESS_SOURCE", agent_version=AGENT_VERSION)

    if await jobs.is_terminal(job_key):
        return ProcessResult.duplicate_suppressed(job_key)

    await jobs.start(job_key, trace_id=trace_id)
    artifact = await artifact_vault.fetch_and_store(event)
    await artifacts.assert_immutable(artifact)

    route = route_registry.for_artifact(artifact)
    if route.is_unavailable:
        return await ledger.record_unavailable(event, artifact, route.reason)

    extraction = await agent_runner.run_structured(
        agent_name=route.evidence_agent,
        payload=route.build_payload(artifact),
        output_model=route.output_model,
        trace_id=trace_id,
    )
    evidence = validator.validate_extraction(extraction, artifact)
    await ledger.append_evidence(evidence, job_key=job_key)

    links = await agents.entity_resolution(evidence, trace_id=trace_id)
    validated_links = validator.validate_links(links, evidence)
    proposals = await agents.case_linker(evidence, validated_links, trace_id=trace_id)

    for proposal in proposals.actionable_case_links():
        case_bundle = await cases.load_frozen_bundle(proposal.case_id, evidence.ids)
        delta = await agents.delta_investigator(case_bundle, trace_id=trace_id)
        reviewed = await agents.quality_reviewer(delta, case_bundle.source_map, trace_id=trace_id)
        validator.assert_review_acceptable(reviewed)
        await ledger.stage_case_update(proposal.case_id, delta, reviewed, job_key=job_key)

    await jobs.succeed(job_key)
    return ProcessResult.succeeded(job_key)
```

The code above intentionally separates agent calls from persistence. An agent result is a **proposal** until `validator` and `ledger` services accept it.

---

## 8. Pydantic Validation Gates

| Gate | Runs after | Required checks |
|---|---|---|
| `validate_source_event` | Adapter discovery | Domain/path allowlist, source ID, canonical URL, external ID, fingerprint, event timestamp. |
| `validate_artifact` | Fetch/store | Content hash, MIME type, GCS/local URI, retrieval time, source linkage, availability state. |
| `validate_extraction` | Document/media agent | Output schema, artifact IDs, anchors, readable source excerpt, status, no PII. |
| `validate_links` | Entity/Case agents | Evidence-backed candidate/confirmed distinction, known case/entity IDs, correction constraints. |
| `validate_delta` | Delta Investigator | Original + later anchor/IDs, neutral language, explicit unknown/conflict states, no causal/legal/allegation language. |
| `validate_review` | Quality Reviewer | All blocking issues resolved or case staged as review required. |
| `validate_approval` | Approval service | Reviewer identity/role, case ID, artifact hash, action type, expiration, one-time use. |

---

## 9. Queue and Event Contracts

Use small, versioned messages. Never pass raw artifact bytes, full transcripts, secrets, or broad corpora through Pub/Sub/Cloud Tasks.

```json
{
  "event_type": "artifact.stored.v1",
  "event_id": "evt_...",
  "trace_id": "trace_...",
  "source_event_id": "src_evt_...",
  "artifact_id": "art_...",
  "idempotency_key": "sha256:...",
  "occurred_at": "2026-08-19T00:00:00Z"
}
```

Cloud Task payloads should contain a job ID and immutable references, not raw content. The worker reloads current job/permissions/state, checks idempotency, and invokes the smallest bounded workflow.

---

## 10. Agent Prompt Strategy

Maintain the global policy contract in `app/policies/global_policy.py` and role prompts in `app/agents/prompts.py`. Concatenate in the factory at runtime:

```text
SYSTEM = GLOBAL_POLICY + "\n\nROLE-SPECIFIC INSTRUCTIONS\n" + ROLE_PROMPT
```

The prompts are defensive by design. They direct every agent to use only supplied artifacts, preserve uncertainty, avoid unsupported allegations/causal claims, refrain from external action, and return only schema-valid data. See `app/agents/prompts.py` for copy-ready strings.

---

## 11. Required Evaluation Fixtures

| Fixture | Expected result |
|---|---|
| `valid_city_delta` | Valid original + later anchors create one staged, review-required delta. |
| `duplicate_event` | Second delivery returns `DUPLICATE_SUPPRESSED`; no duplicate ledger event. |
| `missing_attachment` | Case records `NOT_PUBLISHED`/`REQUEST_NEEDED`; no fabricated excerpt. |
| `conflicting_sources` | Case is `CONFLICTING` with both sources preserved. |
| `candidate_entity` | Link remains `CANDIDATE`, not confirmed. |
| `mps_privacy_block` | Student-level/otherwise prohibited input is rejected before model invocation. |
| `approval_denied` | Packet renderer rejects missing/expired/hash-mismatched approval. |

---

## 12. Implementation Prompts for Claude Code

### Prompt 1 — Initialize contracts and tests

> Read `CLAUDE.md`, the PRD, multi-agent design, and this document. In plan mode, propose the smallest implementation of `backend/app/domain`, `backend/app/schemas`, and deterministic validation services for the reviewed City replay corpus. Include exact Pydantic schemas, unit test files, fixture requirements, and acceptance criteria. Do not add ADK, FastAPI, Cloud, or source retrieval code until the plan is approved.

### Prompt 2 — Add the first bounded agent

> Read the established contracts and `docs/architecture/multi-agent-design-and-prompts.md`. In plan mode, propose an ADK-backed Document Evidence Agent with a version-isolated `AgentRunner`, read-only artifact tools, structured Pydantic output parsing, source-anchor validation, local fake runner tests, and no storage mutation tools. Verify current ADK APIs against installed documentation before coding.

### Prompt 3 — Add deterministic workflow

> In plan mode, propose the City source-event worker path: `SourceEvent → ArtifactVault → route → Document Evidence Agent → validator → in-memory ledger`. Include idempotency, duplicate-event, and missing-source tests. Do not add live scheduler/queue/cloud deployment until the local replay path passes.
