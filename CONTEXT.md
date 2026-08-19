# CivicTrace Shared Language

This file defines the compact vocabulary used in CivicTrace code, tickets, specifications, tests, and agent prompts. Prefer these terms over generic substitutes.

| Term | Meaning | Do not use it to mean |
|---|---|---|
| **Artifact** | Immutable local copy plus provenance metadata for one approved public source version. | A model summary or unpreserved URL. |
| **Anchor** | Precise evidence pointer: PDF page, table row, JSON field, media timestamp, or map feature. | A broad citation without location. |
| **Evidence** | A validated, anchor-backed statement extracted from an artifact. | A model belief, confidence score, or speculation. |
| **Promise** | A public commitment, vote, target, allocation, obligation, or stated outcome documented in an official source. | A political intent not anchored in the record. |
| **Promise Ledger** | The durable case record that connects a Promise to later public evidence and unresolved gaps. | A general chat history or generic database table. |
| **Case** | One bounded civic-accountability inquiry with defined scope, entities, evidence, states, and human owner. | A citywide topic without boundaries. |
| **Decision Delta** | A structured comparison of an original Promise and later public record, with explicit anchors and uncertainty. | An accusation, verdict, or causal finding. |
| **Evidence Trace** | A user-visible audit trail of stored artifacts, validated extraction, agent proposals, policy checks, and required human decisions. | Raw hidden chain-of-thought or private model reasoning. |
| **Unknown** | The evidence is insufficient to establish a required fact. | A negative conclusion. |
| **Not Published** | Expected public artifact is absent or unavailable at the source. | Proof that an event did not happen. |
| **Candidate Link** | A conservative, unconfirmed connection between an artifact/evidence item and a Case or entity. | A durable Case relationship. |
| **Approved source** | A source domain/type/purpose explicitly allowed by source policy and represented in a reviewed fixture. | Any public webpage. |
| **Human approval** | A time-limited, case-bound decision authorizing a specific draft-only external-facing artifact. | An LLM output, button click without audit, or blanket permission. |
| **Source replay** | Deterministic reprocessing of a reviewed public corpus/fixture for testing and demo reliability. | Live browsing of arbitrary sites. |
| **Material claim** | A user-visible statement affecting a Promise, Decision Delta, source state, or proposed inquiry. | Navigation text or non-factual UI copy. |

## MVP Boundary

The City of Milwaukee Promise Ledger replay loop is the only MVP critical path. It processes a reviewed City source bundle, preserves its artifacts, extracts anchored evidence, updates one bounded Case through deterministic validation, and renders a Decision Delta or explicit uncertainty for human review.

MPS is a later, public-institutional-data-only extension. No individual student data belongs in CivicTrace.

## Naming Rules

- Use `artifact_id`, `evidence_id`, `case_id`, `promise_id`, `anchor`, `decision_delta`, `evidence_trace`, `approval_token`, `source_policy`, and `source_replay` in schemas and ticket names.
- Use `propose_*` for agent-produced structured proposals. Use `validate_*`, `stage_*`, or `approve_*` for deterministic/human-controlled transitions.
- Never name an agent, class, component, or UI state `truth`, `judge`, `detect_corruption`, `investigate_crime`, or `publish`.
- User-facing uncertainty states are uppercase: `UNKNOWN`, `NOT_PUBLISHED`, `CONFLICTING`, `CANDIDATE_LINK`, `REQUEST_NEEDED`, and `HUMAN_REVIEW`.
