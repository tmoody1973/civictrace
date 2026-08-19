# CivicTrace Meeting Monitor and MPS Expansion

## Decision: Add the Meeting Monitor—But Make It the Sensor, Not the Product

**Yes, add the local-government meeting monitor.** It is a perfect CivicTrace capability because it creates a continuous source of fresh, multimodal evidence. But a transcript plus a short summary is an increasingly common pattern. CivicTrace becomes distinctive only when the monitor feeds a durable accountability system that remembers what an institution promised, detects what changed, and connects a later meeting to the source record that makes it meaningful.

> **The meeting monitor captures what happened today. CivicTrace remembers whether it changed what was promised last year.**

The agent should create a short digital brief after each monitored public meeting, but public publication must be **human-approved**. This is both safer and stronger: the agent can reliably assemble the complete brief in the background, while a reporter, editor, civic organization, or designated public-information staff member remains accountable for public-facing language.

## The Correct Media Pipeline

Use **Google Cloud Speech-to-Text batch recognition** as the primary meeting-transcription service. Its official documentation describes asynchronous recognition of long audio stored in Cloud Storage, with long-running operations and output written back to Cloud Storage; the documented upper limit is 480 minutes.[1] This fits the required Gemini + Google Cloud stack more cleanly than adding Deepgram as the critical dependency.

| Stage | Service | Work completed asynchronously | Durable artifact |
|---|---|---|---|
| **Discover** | MPS Board / IC Board / E-Notify or City Legistar adapter | Detect a new agenda, recording, or final minutes update. | `SourceEvent` with source URL, fingerprint, and timestamps. |
| **Preserve** | Cloud Storage + Firestore | Download or store allowed public media/document metadata; hash and retain raw evidence. | Immutable source artifact and retrieval record. |
| **Transcribe** | Cloud Tasks + Speech-to-Text batch | Submit the long recording in Cloud Storage; poll or receive operation completion. | Timestamped transcript linked to media. |
| **Understand** | Gemini 3.5 Flash through ADK | Extract structured decisions, votes, commitments, action items, speakers, amendments, and open questions with source anchors. | Typed `MeetingFact` objects and evidence citations. |
| **Connect** | Firestore case graph + BigQuery retrieval | Link the facts to prior Board decisions, school improvement commitments, budget/contract records, school/facility identifiers, and outcome data. | Updated Accountability Graph. |
| **Act** | ADK planner + approval-gated artifact worker | Draft a digital meeting brief, highlight cases affected, and prepare a specific question/request for unresolved material changes. | Staged brief + editor approval request. |
| **Publish** | Human-gated destination adapter | An editor approves the brief for a newsroom CMS, newsletter, community feed, or internal civic-monitoring workspace. | Immutable approval and publish audit record. |

### The Five Sections of a CivicTrace Meeting Brief

The brief must not be a generic “meeting notes” product. It should be a compact, evidence-first operational record.

| Section | What it contains | Why it is differentiated |
|---|---|---|
| **What changed** | Passed, deferred, amended, or newly introduced decisions with vote/status. | Anchors the brief in institutional action rather than conversation. |
| **Promise ledger updates** | Existing commitments that were advanced, revised, contradicted, or left unresolved. | Creates longitudinal accountability. |
| **Action items** | Responsible public body, due signal, and next record expected. | Turns discussion into a future watch task. |
| **Evidence clips** | Precise agenda page/table, transcript segment, and video/audio timestamp. | Lets an editor verify before publishing. |
| **Watch next** | The source/document/meeting that would confirm, contradict, or complete the case. | Makes the agent proactive instead of retrospective. |

## Milwaukee Public Schools Is a High-Value Vertical

MPS is not merely another source to ingest. It can become CivicTrace’s first **Education Accountability** vertical: a product for reporters, parent advocacy groups, education nonprofits, and district-facing transparency teams that follows public school commitments from Board action to publicly reported aggregate outcomes.

MPS’s Board is the district’s policy-making body. MPS publicly directs users to its Electronic School Board/IC Board calendar for agendas, livestreaming, and testimony details; it provides access to prior-meeting proceedings and audio recordings, and uses City E-Notify for Board and committee notices.[2] MPS also publishes 2024–27 school improvement-plan summaries and links district/state report-card resources, explicitly describing continuous improvement as planning, implementation, evidence collection, study of progress, and adjustment.[3]

That produces the ideal civic loop:

> **Board commitment → implementation plan → public budget/contract/facility record → aggregate school or district outcome → next Board discussion.**

### The First MPS Product Wedge: School Promise Ledger

Do not begin with every student, every classroom, or a prediction system. Start with one public institutional promise. A strong initial case is a Board/committee action connected to a 2024–27 school improvement plan, a public facility/capital project, or a public contract. CivicTrace then follows the published lifecycle and keeps the stakeholder-facing evidence in one place.

| Evidence layer | Possible public source | Agent question |
|---|---|---|
| **Commitment** | MPS Board agenda, minutes, vote, hearing audio/video, or improvement-plan summary. | “What did the Board or district publicly commit to, for whom, and by when?” |
| **Implementation** | Public budget, Board follow-up, school improvement material, executed contract/award/tabulation, facility plan. | “What action, funding, vendor, or operational milestone was publicly documented?” |
| **Aggregate outcome** | MPS district/school report cards, Wisconsin DPI public data, published plan-progress documents. | “What public aggregate indicator or official progress evidence is available later?” |
| **Uncertainty** | Missing update, delayed attachment, conflicting Board statement, unavailable contract record. | “What is not yet established by the public record, and what is the narrow next question?” |

The product must state **correlation, not causation**. It can say, “The plan committed to X; the later public report lists Y,” but it must not claim that a vendor, policy, teacher, school, or student caused a change unless a valid source explicitly establishes that fact.

### MPS Procurement: Valuable but Not P0

MPS now routes active bids and RFP submissions through Euna Procurement, while its public page points vendors to E-Notify and related materials.[4] Therefore, do not build your core hackathon demo around scraping live bid workflows. Use public Board materials, published tabulations/awards, executed-contract materials, or a curated public procurement artifact. The agent should prove it can ingest a contract when available—not bet the demo on a dynamic vendor portal.

## Privacy and Safety Boundary

This is an institutional transparency product, never a surveillance or risk-scoring system.

| Never ingest or infer | Allowed public evidence |
|---|---|
| Individual student attendance, grades, discipline, disability, health, family, address, or other personally identifiable records | Public Board materials, public meeting audio/video, published school improvement plans, public budgets/contracts, aggregate school/district report cards, publicly available facilities/operations documents |
| Student-level prediction, profiling, or intervention recommendation | Source-cited institutional promise tracking and public aggregate-outcome comparisons |
| Automatic claims about educator, school, or vendor wrongdoing | Explicit evidence states: supported, conflicting, incomplete, or unknown; human-reviewed public brief |

## The One-Minute MPS Demo Extension

After the City of Milwaukee core demo, add a 30–45 second sequence:

1. The MPS source watcher detects a new Board agenda or public recording.
2. The media worker transcribes the meeting in the background and extracts a Board commitment/action item with a timestamp.
3. The MPS Promise Ledger recognizes a related published improvement plan or public facilities/budget artifact.
4. The Evidence Studio shows the exact meeting clip, source page, timeline, and published aggregate outcome link.
5. The agent stages a brief: “This Board action updated case MPS-014. The next expected public evidence is the next plan-progress or Board report.”

This proves that CivicTrace’s architecture is a **multi-institution public-evidence platform**, while keeping the City core loop polished.

## What to Claim in the Pitch

**Strong and defensible:**

> “CivicTrace monitors the public record of Milwaukee institutions—City Council and the MPS Board—then turns recordings, documents, data, and time into a human-verifiable account of what was promised and what record should come next.”

**Do not claim:**

> “CivicTrace knows why student outcomes changed,” “CivicTrace predicts school failure,” or “CivicTrace automatically publishes the truth.”

## References

[1]: https://docs.cloud.google.com/speech-to-text/docs/batch-recognize "Google Cloud Speech-to-Text — Transcribe long audio files into text"

[2]: https://www.milwaukeepublicschools.org/about/board "Milwaukee Public Schools — Board of School Directors"

[3]: https://www.milwaukeepublicschools.org/about/directory/academics/research-assessment-data/performance-improvement "Milwaukee Public Schools — School Performance and Improvement"

[4]: https://www.milwaukeepublicschools.org/about/directory/finance/procurement-risk-management/vendors/bids-rfps "Milwaukee Public Schools — Bids and RFPs"
