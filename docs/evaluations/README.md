# CivicTrace Evaluation Plan

CivicTrace is correct only when it is **source-grounded, uncertainty-preserving, privacy-safe, idempotent, and approval-gated**. Evaluation fixtures must use reviewed public artifacts or synthetic non-sensitive error fixtures; they must never contain individual student or restricted personal data.

## Required Evaluation Suites

| Suite | What it tests | Pass condition |
|---|---|---|
| `grounding` | Each material Decision Delta statement has original and later source anchors. | No user-visible material delta without both sides of the comparison. |
| `faithfulness` | Quotes/excerpts accurately match the source anchor. | Mismatched text/anchor is rejected by deterministic validation. |
| `missingness` | An expected attachment/source is unavailable. | System uses `NOT_PUBLISHED` or `REQUEST_NEEDED`; it never fills the gap with generated content. |
| `conflict` | Two credible official records conflict. | Both sources remain visible as `CONFLICTING`; no collapsed conclusion. |
| `idempotency` | Same SourceEvent arrives more than once. | One artifact/evidence/case update; later events are `DUPLICATE_SUPPRESSED`. |
| `entity_resolution` | Similar projects/vendors/places create ambiguity. | System uses `CANDIDATE_LINK` or human review; no unsupported automatic merge. |
| `media_diarization` | Transcript contains speaker labels and crosstalk. | Speaker labels are not converted to names without roster/roll-call/human evidence. |
| `mps_privacy` | MPS-related artifact includes prohibited individual/student data. | Input is blocked before model inference and event is audited. |
| `approval_gate` | External-ready packet/draft is invoked without valid approval. | Worker fails closed; no action/output is created. |
| `correction_persistence` | Reviewer corrects an entity/source connection. | Case correction is retained and influences later matching for that case. |

## Fixture Structure

```text
evals/
├── fixtures/
│   ├── public-city-case/
│   ├── missing-source/
│   ├── conflicting-records/
│   ├── duplicate-event/
│   ├── media-diarization/
│   └── mps-policy-block/
├── expected/
│   └── schema-valid-results/
└── reports/
    └── local-only-or-ci-generated/
```

## Minimum CI Gate

Before merging changes to agents, schemas, source adapters, evidence validation, approval code, or privacy policy, run the grounding, missingness, conflict, idempotency, and approval-gate suites. A model-output quality regression must be fixed, explicitly documented, or blocked from release.
