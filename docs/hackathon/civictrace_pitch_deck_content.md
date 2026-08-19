## Cover

# CivicTrace

**The public-evidence engine that wakes up when a promise changes**

All Things Agentic Hackathon · The Taskmaster

## Slide 1

# Public accountability has a capacity problem

- Critical facts are scattered across agendas, PDFs, video, budgets, procurement records, data portals, and months of follow-up.
- The staff who must reconstruct that chain are disappearing: more than 3,200 U.S. print newspapers have closed since 2005.[1]
- A public decision can be visible on vote day—and effectively untraceable by the time implementation begins.

## Slide 2

# Search finds documents. It does not preserve accountability.

| Existing capability | The missing capability |
|---|---|
| Meeting summaries | A memory of what was promised |
| Public-records search | Evidence linked across time and formats |
| Agenda publication | Detection of material change or missing evidence |
| Request management | A narrow, human-approved next question |

> CivicTrace creates a durable case file that tells an editor **what changed, what the record establishes, what remains unknown, and what to ask next.**

## Slide 3

# CivicTrace turns a promise into a living case file

1. An official City source changes.
2. The system stores the original record before any AI reasoning.
3. Specialized agents extract anchored evidence and compare it to an earlier commitment.
4. A reviewer receives a source-linked **Decision Delta** and may approve a bounded inquiry packet.

**No allegation engine. No auto-publication. No mystery sources.**

## Slide 4

# Milwaukee is the right proving ground

- The City provides public legislative records through Legistar and a City open-data portal.[2] [3]
- The first build is intentionally narrow: **one geographically bounded public commitment** and its later public evidence.
- A local pilot makes the product credible now—and the source-adapter architecture makes it repeatable across cities later.

## Slide 5

# The Evidence Studio makes AI conclusions inspectable

- **Original source pane:** a public PDF, table, meeting transcript, or video clip—not a hidden model summary.
- **Decision Delta pane:** original commitment beside later evidence, plus explicit `Unknown` and `Conflicting` states.
- **Promise Ledger timeline:** commitment → later record → evidence gap → human-approved next inquiry.
- Every material statement opens the exact page, row, or timestamp that supports it.

## Slide 6

# This is autonomy with institutional guardrails

| Autonomous | Never autonomous |
|---|---|
| Source monitoring and event detection | Publication, outreach, or records-request submission |
| Artifact preservation and bounded extraction | Firestore case mutation by a model |
| Case-link and delta proposals | Approval-token grant |
| Async retry, replay, and source-health tracking | Unsupported civic conclusions |

**The model proposes. Deterministic code validates. Humans decide.**

## Slide 7

# The architecture is designed for trust under load

- **Cloud Storage:** immutable public artifacts, content hashes, and provenance.
- **Pub/Sub + Cloud Tasks:** durable, idempotent background work; duplicate events become one case update.
- **ADK + Gemini Flash:** specialized agents reason over only the bounded evidence bundle.
- **Firestore + BigQuery:** durable case ledger plus high-volume public-data filtering before model context.
- **Cloud Run:** scale-to-zero API and internal worker services with traceable job lineage.

## Slide 8

# A constrained agent team does the heavy lifting

| Agent | Bounded contribution |
|---|---|
| Document / Media Evidence | Extracts source-anchored facts from PDFs, tables, transcripts, and clips |
| Entity Resolution / Case Linker | Proposes conservative connections to public projects, places, vendors, and cases |
| Delta Investigator | Compares original commitment with later evidence |
| Quality Reviewer | Rejects unsupported, privacy-risky, causal, or politically loaded outputs |
| Inquiry Planner / Brief Builder | Drafts the narrowest next question or a review-required brief |

The orchestrator owns routing, retries, schemas, ledger writes, and approvals—**not an LLM.**

## Slide 9

# Multimodality is necessary, not decorative

- A promise may be in an agenda PDF.
- Its qualification may appear in a timestamped meeting clip.
- Its funding or execution may appear in a structured public record.
- Its public context may be geographic and visible on a map.

CivicTrace synchronizes these forms of evidence so a human can test the conclusion rather than trust a generated summary.

## Slide 10

# City first. MPS demonstrates platform reach.

**Hackathon core — Milwaukee City Promise Ledger**

A reliable source-to-inquiry loop using City records and one real public case.

**Demonstration extension — MPS Promise Ledger**

Public Board commitments → public improvement, budget, facility, or award artifacts → public aggregate progress evidence.

> The MPS extension contains **no individual student data, no prediction, and no profiling.**

## Slide 11

# CivicTrace is built to compete on all three axes

| Evaluation axis | Visible proof |
|---|---|
| **The Taskmaster** | One source event autonomously becomes an evidence-linked, human-reviewable inquiry workflow. |
| **Best Architectural Design** | Immutable artifacts, typed agents, idempotency, dead-letter/replay behavior, approval tokens, and traceable operations. |
| **Best Multimodal UX** | Synchronized document, table, transcript/video, timeline, map context, and evidence graph. |

The project is designed as a real newsroom/civic-research product—not a hackathon-only chat demo.

## Slide 12

# The four-minute proof

1. A real Milwaukee source event enters the system.
2. Background tasks preserve and process documents/data.
3. CivicTrace opens a Decision Delta with exact evidence anchors.
4. The reviewer corrects a link, sees the evidence update, and approves a narrow inquiry packet.
5. A duplicate event produces no duplicate output; a missing attachment becomes an explicit uncertainty state.
6. Cloud logs and trace show the full asynchronous job lineage.

## Slide 13

# From one Milwaukee promise to civic infrastructure

**CivicTrace gives resource-strapped public-interest teams a persistent, inspectable memory of what institutions said they would do.**

Every public promise should have a traceable record of what happened next.

## Slide 14

# References

[1] Northwestern Medill Local News Initiative, *The State of Local News 2024* — https://localnewsinitiative.northwestern.edu/projects/state-of-local-news/2024/report/

[2] City of Milwaukee Legistar — https://milwaukee.legistar.com/Calendar.aspx

[3] City of Milwaukee Open Data — https://data.milwaukee.gov/

CivicTrace product, architecture, and evaluation details: `docs/product/PRD.md`
