# CivicTrace Competition Requirements

## The Rule: Build One System, Prove Four Things

CivicTrace should not be built as a polished local-government chat interface. To compete, every meaningful product feature must serve **four visible proofs at once**: autonomous work, scalable data handling, disciplined architecture, and multimodal understanding. The core submission category is **Taskmaster**; the architecture and experience must be strong enough that the same system is credible for the specialty awards.

| Competition signal | What judges need to see | CivicTrace non-negotiable | What does **not** count |
|---|---|---|---|
| **Taskmaster / operational utility** | The agent intercepts and completes a multi-step background workflow without a person guiding every step. | Scheduled source watcher → ingestion → extraction → graph update → material-change detection → evidence-case assembly → human-approved inquiry packet. | A user asks a question and receives a summary. |
| **Massive datasets / asynchronous work** | The system visibly handles a corpus too large or slow for a single request-response interaction. | A historical Milwaukee civic corpus is partitioned, queued, resumable, and processed into a durable evidence graph; new records trigger incremental runs. | Uploading one PDF to a model or showing a progress spinner. |
| **Best Architectural Design** | Decoupled systems, state management, fault tolerance, scoped tools, security, and clear engineering trade-offs. | Immutable evidence ledger, idempotent jobs, typed state machine, isolated workers, source provenance, retry/dead-letter behavior, and approval-gated external action. | A long list of cloud services or an unreadable microservices diagram. |
| **Best Multimodal UX** | The user can understand and challenge a complex reality through multiple essential media types. | A visual-and-auditory evidence experience that aligns agenda PDF clauses, meeting-video/audio clips, structured records, maps, and timeline deltas. | A chat window that accepts PDFs and displays text. |
| **Production readiness** | Live proof, reproducible repository, deploy evidence, and documentation that makes the system trustworthy. | Cloud Run deployment, Google Cloud console proof, real public-source replay, README, architecture diagram, test suite, and a short failure/recovery demonstration. | A mock-only UI or unverified demo narration. |

## Required Acceptance Tests

The team should not call CivicTrace “ready” unless it passes every test below.

| Test | Pass condition | Prize value |
|---|---|---|
| **Corpus replay** | A fresh environment can ingest a documented corpus manifest, persist raw artifacts, and finish a background run without a browser remaining open. | Proves scale and autonomy. |
| **Incremental update** | A newly discovered agenda, meeting item, or data record triggers only the required downstream work; it does not rerun the full corpus. | Proves event-driven efficiency and cost discipline. |
| **Idempotent replay** | Re-delivering the same source event leaves exactly one evidence item and one terminal job result. | Proves architecture maturity. |
| **Grounded decision delta** | Every claim on the Decision Delta cites a source ID and location such as page/table cell, timestamp, or dataset row. | Proves trustworthy data synthesis. |
| **Conflict and missingness** | A contradictory source or missing attachment creates a visible `CONFLICTING` or `NOT_PUBLISHED` state, never a fabricated conclusion. | Proves safety and fault tolerance. |
| **Approval boundary** | The system can draft a records-request or source-question packet, but it cannot send, file, publish, or contact anyone without a specific approval token. | Proves properly scoped tools. |
| **Multimodal correction** | An editor can correct a source association or focus signal directly on a PDF, video timestamp, map, or graph node; that feedback persists into future alerts. | Proves multimodal UX and adaptive collaboration. |

## Success Metric for the Demo

The system must end its demo with a result an ordinary assistant cannot create:

> **A source-grounded inquiry case showing that a Milwaukee public commitment has a newly detected, evidence-linked change or unresolved gap, together with the precise next record or question needed to resolve it.**

The case may never allege misconduct. Its power is in making a verifiable gap visible, preserving the chain of evidence, and doing the preparatory work that a human newsroom or civic watchdog often cannot sustain.

## Contest Facts to Design Around

The official rules weight **Innovation & Operational Utility (40%)**, **Architectural Discipline & Tech Stack (30%)**, and **Demo & Production Readiness (30%)**. They state that Taskmaster entries should intercept and complete multi-step background workflows, and they call out modularity, state, isolated/scoped tools, and failure tolerance as architectural signals. The rules also designate Best Architectural Design and Best Multimodal UX for top-scoring projects in their respective criteria, while allowing each project to receive up to one prize.[1]

## Reference

[1]: https://allthingsagentichackathon.devpost.com/rules "All Things Agentic Hackathon — official rules, judging, and prizes"
