# CivicTrace: Four-Minute Demo and Repository Proof Plan

## Demo Setup Before Recording

Record against a pre-validated Milwaukee replay corpus. The source event must be real and publicly available, but the demo should re-emit it through the system rather than depend on a live third-party site responding on cue. Keep the raw source files, source hashes, and retrieval dates in the repository’s corpus manifest. Every screen in the recording must show actual application state, not a mocked animation.

| Preflight item | Required proof |
|---|---|
| Corpus manifest | Lists public source URL, retrieval timestamp, SHA-256, artifact type, and replay order. |
| Starting case | One real Council/committee commitment linked to an address, project, or identifiable public initiative. |
| Later evidence | At least one later official record that changes, qualifies, or fails to establish a promised milestone. |
| Media bundle | A source PDF/table, meeting video or audio clip with timestamp, structured City record, and location/map evidence. |
| Failure fixture | A legitimate missing/unavailable attachment or a controlled test source that causes an explicit `NOT_PUBLISHED` state. |
| Resilience fixture | A duplicate source-event message with the same idempotency key. |
| Google Cloud proof | Deployed Cloud Run service, Firestore data, Cloud Storage artifacts, job queue, and at least one trace/log view. |

## Four-Minute Recording Script

| Time | Visual | Narration / action | Proof category |
|---:|---|---|---|
| **0:00–0:15** | Milwaukee map fades into the Civic Memory Console with real corpus counters. | “Public promises are made in meetings, then scattered across years of files, contracts, and service records. CivicTrace keeps the evidence alive.” | Problem and scale. |
| **0:15–0:35** | Re-emit a real City Legistar source-change event. A watcher detects the fingerprint and creates a job graph. | “A new public record arrived. No one prompted the agent; the territory watcher opened a durable investigation workflow.” | Taskmaster trigger. |
| **0:35–1:00** | Queue stages advance: raw artifact persisted, document parsed, video clip aligned, city data query completed. | “The workers separate retrieval, multimodal extraction, entity resolution, and evidence updates so a failure in one source cannot corrupt the case.” | Asynchronous heavy lifting. |
| **1:00–1:40** | Decision Delta Studio: click promise clause in PDF; meeting clip jumps to timestamp; map shows project location; timeline reveals later record. | “This is not a summary. Each statement is anchored to the original clause, hearing moment, place, and later public record.” | Multimodal UX. |
| **1:40–2:10** | Show `DecisionDelta`: promise, changed/unknown evidence, and “what would change this conclusion?” | “CivicTrace found a gap in the record—not an accusation. It knows what it can prove, what it cannot, and the exact record needed next.” | Grounding and safety. |
| **2:10–2:35** | Editor approves the proposed inquiry; Artifact Worker creates an evidence packet and draft question. | “The agent takes the heavy lifting to a completed, reviewable artifact. An editor retains authority over outreach and publication.” | Full workflow / scoped action. |
| **2:35–2:55** | Deliver the same source event again. UI shows duplicate delivery; ledger remains at one evidence item. | “Public feeds are at-least-once. CivicTrace is idempotent: we received the event twice and created the evidence once.” | Architectural Design. |
| **2:55–3:15** | Open missing-attachment fixture and trace. UI shows `NOT_PUBLISHED → REQUEST_NEEDED`; no claim appears. | “When a source is missing, the agent preserves uncertainty and creates a bounded next action instead of hallucinating.” | Fault tolerance. |
| **3:15–3:40** | Google Cloud Console: Cloud Run, Pub/Sub/Tasks, Firestore, Storage, BigQuery, Cloud Logging/Trace. Then architecture diagram. | “This is deployed on Google Cloud. Here is the live service, durable state, event infrastructure, and trace for the exact case you just saw.” | Production readiness. |
| **3:40–4:00** | Return to finished inquiry packet and source graph. | “CivicTrace does not generate a story. It gives communities a persistent, evidence-backed way to ask the question no one had capacity to keep asking.” | Closing. |

## Repository Structure That Judges Can Trust

```text
civictrace/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── architecture-diagram.mmd
│   ├── decision-records/
│   │   ├── 001-event-ledger.md
│   │   ├── 002-approval-boundary.md
│   │   └── 003-source-provenance.md
│   └── demo-replay.md
├── apps/
│   ├── api/                 # Cloud Run source watcher + query API
│   └── studio/              # Evidence Studio interface
├── workers/
│   ├── extractor/           # Gemini + ADK structured extraction
│   ├── resolver/            # entity/place resolution
│   ├── delta/               # decision-delta investigation
│   └── artifact/            # inquiry packet generator
├── packages/
│   ├── schemas/             # typed Evidence/Claim/Delta/Job contracts
│   └── source-adapters/     # Legistar, CKAN, and file adapters
├── infra/                   # Cloud Run, Pub/Sub, Tasks, Storage, Firestore
├── corpus/
│   ├── manifest.jsonl       # source URLs, hashes, metadata
│   └── fixtures/            # allowed replay sources and test fixtures
└── tests/
    ├── test_grounding.py
    ├── test_idempotency.py
    ├── test_approval_gate.py
    └── test_missingness.py
```

## The README Must Answer Five Questions in the First Screenful

1. **What does the agent do without a user prompt?** It watches public sources and runs the evidence-to-inquiry workflow.
2. **Why is this not a chatbot?** It maintains durable public-source state, handles a historical corpus, and produces a reviewed action artifact.
3. **Why can users trust it?** Every conclusion has source anchors, uncertainty is explicit, and side effects are approval-gated.
4. **How is it deployed?** Gemini + ADK + Google Cloud services, with a concrete local replay and Cloud Run deployment path.
5. **How can a judge verify it?** One command replays the documented Milwaukee source bundle and runs the test suite.

## Submission Image and Video Checklist

The Devpost page should include the architecture image, one annotated Evidence Studio screenshot with all media visible, one screenshot of the job/ledger state, one Cloud Run or Console screenshot, and the four-minute video. The video must show the actual deployed backend on Google Cloud, as the official rules require.[1]

## Reference

[1]: https://allthingsagentichackathon.devpost.com/rules "All Things Agentic Hackathon — official submission and judging requirements"
