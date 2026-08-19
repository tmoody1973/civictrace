# CivicTrace in Milwaukee: Go/No-Go Decision

## Verdict: **Go—Build in Milwaukee, but Narrow the Wedge**

Use **the City of Milwaukee as CivicTrace’s first territory**, with Milwaukee County as an optional second jurisdiction. Do not choose Milwaukee because it has the most data; it does not. Choose it because it offers a credible technical backbone, a manageable civic surface area, and a product narrative with a personal point of view: **CivicTrace makes it possible for one local reporter, community newsroom, or neighborhood organization to keep a promise from disappearing after a vote.**

The best first product is **The Milwaukee Promise Ledger**: an agent that follows one kind of city commitment—beginning with a development agreement, tax-increment financing decision, or capital-project vote—from Council action through publicly observable money, property/permit, service, and milestone records. It does not claim that anyone acted improperly. It shows the evidence trail, identifies what is still unknown, and prepares the next lawful, human-approved inquiry.

> **Product sentence:** *CivicTrace is an accountability engine for Milwaukee that turns every public promise into a living, evidence-linked case file—and wakes up when the record changes.*

## Is Anyone Building Something Similar?

**Yes, but the relevant market is fragmented.** This is not a reason to abandon the idea; it tells you exactly what CivicTrace must not be.

| Existing product / initiative | What it genuinely does | Why CivicTrace is still different |
|---|---|---|
| **Agenda Watch / Big Local News** | Aggregates and makes public meeting documents searchable for local reporters. Agenda Watch describes itself as a way for reporters and the public to search government agenda documents across supported regions and platforms.[1] | CivicTrace must go beyond “search the agenda.” It must link a meeting decision to a promise, a location/project, a vendor/spend signal, later operational evidence, and a next inquiry—then maintain that case over time. |
| **Documenters** | Uses trained, paid community members to cover under-reported public meetings and publish structured notes. | CivicTrace can make Documenters more powerful by preparing the evidence packet before a meeting and turning the resulting notes into a durable case after it. It does not replace human civic reporting. |
| **MuckRock** | Provides public-records request filing, correspondence tracking, and document publication infrastructure. | CivicTrace should use or complement a records-request platform. Its distinctive task is deciding, from the evidence graph, what precise missing record would resolve an open question; any actual request is editor-approved. |
| **Council Data Project** | Makes council documents, transcripts, legislation, and votes searchable in participating jurisdictions. | CivicTrace adds active, longitudinal oversight: it tracks what happens **after** legislation moves, including funding, delivery, service conditions, and unresolved promises. |
| **Granicus and CivicPlus** | Help public agencies manage agendas, meetings, documents, and public publishing. | These are government operations systems. CivicTrace is an independent, public-interest intelligence layer that follows the public record across agencies and outcome sources. |

The closest direct analogue is **Agenda Watch**, and it is useful validation. Its own description focuses on collecting and searching government documents, with support for platforms including Legistar, Granicus, CivicClerk, and PrimeGov.[1] CivicTrace can use the same kind of source adapter, but it must make a materially different promise:

> **Agenda Watch tells you which documents mention a topic. CivicTrace tells you what a government promised, what changed afterward, what evidence supports that conclusion, and what question must be answered next.**

## Milwaukee Data Reality

Milwaukee has enough data to ship the real agent loop. The relevant question is not whether every municipal record is perfect; no city meets that standard. It is whether the first case can use stable, public, machine-readable evidence.

| Capability | Evidence found | Status for the hackathon |
|---|---|---|
| **City datasets** | Milwaukee’s CKAN portal groups data across elections/campaign, housing/property, maps, public safety, and city services, and publishes a catalog/API surface.[2] A live CKAN catalog request returned data successfully. | **Ready.** Use City property, address, zoning, service, and budget-adjacent records as the core evidence layer. |
| **City legislative events** | The City uses a public Legistar calendar; a live `webapi.legistar.com/v1/milwaukee/events` response returned a Common Council event with stable IDs, date/time, final agenda/minutes status, video status, and official meeting URL. | **Ready.** Use an event watcher to discover Council/committee actions, then retrieve available items and attachments. |
| **County legislative events** | Milwaukee County exposes a public Legistar calendar and a live `webapi.legistar.com/v1/milwaukeecounty/events` request returned an event record. | **Ready as an adapter**, but keep it out of the core demo unless the selected case crosses jurisdictions. |
| **Spending / vendor evidence** | The City publishes an Open Checkbook surface. Its dynamic rendering needs export/API validation before it can drive a production agent. | **Use as a seeded corroborating source** in the demo, not as a live dependency. |
| **County data** | The County has an open-data portal with downloadable/GIS-oriented data. | **Use for contextual enrichment**—transit, parks, facilities, geography—not as the primary case system. |

### The Technical Caveat Is a Feature, Not a Weakness

Some meeting files will be absent, delayed, scanned, or incomplete. The agent should never silently fill a gap. Give it explicit evidence states: `SOURCE_FOUND`, `EXTRACTED`, `CONFLICTING`, `NOT_PUBLISHED`, `REQUEST_NEEDED`, and `HUMAN_REVIEW`. A missing agenda attachment then becomes a meaningful action in the case, not a broken demo.

## The First Milwaukee Demo: **Promise → Project → Public Reality**

Start with **one City Council or committee decision** tied to a geographically bounded project. The specific underlying case can be chosen after a quick document review; do not choose it because it sounds scandalous. Choose a record set with a clean, sourceable sequence and an obvious public promise.

| Phase | Source type | Agent behavior | Output |
|---|---|---|---|
| **1. Observe the promise** | City Legistar agenda, file, vote, resolution, and meeting video/status | Extracts the project, location, entities, public commitment, target dates, funding language, and uncertainty. | A cited `Commitment` node, never a free-form summary. |
| **2. Connect the project** | City property/address/zoning layers; public project/permit or service records | Resolves the project to an address/parcel/district and builds a time-aware project record. | A visual place-and-time thread. |
| **3. Follow the money or execution signal** | Seeded Open Checkbook/vendor/contract record; City capital/budget material | Links a vendor/department/funding reference only when it is source-supported. | An evidence card with the exact source field and confidence. |
| **4. Check public reality** | City service/311-type records, inspection data where available, later meeting documents, public comment/video | Detects an unresolved milestone, changed deadline, or persistent condition. It does **not** infer corruption or causality. | A `Decision Delta`: *what was promised; what later record says; what remains unverified.* |
| **5. Take a bounded next action** | The case graph plus a source template | Produces a journalist/editor review packet: citations, video timestamps, a chronological record, and a draft question or narrow records-request outline. | A human-approved inquiry—not an automated allegation or filing. |

### The Four-Minute Demo Moment

Show a real historical City Council file and its original promise. The agent pulls its city/project identifiers, renders the promise as a traceable node, then ingests a later record that changes the timeline, status, or delivery evidence. The graph lights up a **Decision Delta** and asks an editor: “The public record does not yet establish whether milestone X occurred. Approve a request for exhibit Y?” The editor approves; a research packet and a source-specific request draft appear.

That moment is powerful because it shows an agent creating a **new, verifiable piece of civic capacity**. It is neither a chat answer nor an auto-written news article.

## What to Build and What Not to Build

| Build for the hackathon | Do not build yet |
|---|---|
| One City Legistar watcher and event/item adapter | Every City and County committee scraper |
| One curated historic project case, with replayable official records | A citywide corruption detector |
| Typed Accountability Graph: `Commitment`, `Decision`, `Project`, `Vendor`, `Evidence`, `Unknown`, `Inquiry` | Unverified automated claims or public publishing |
| Multimodal evidence: agenda PDF/table, meeting/video clip, map/location, structured data record | Live access to every dynamic spending or procurement portal |
| A human-approval gate for a records-request/question packet | Filing requests or contacting sources autonomously |
| Cloud Run + Firestore + ADK/Gemini asynchronous watcher and audit log | A generic local-news dashboard |

## Build Recommendation

Submit to **The Taskmaster** track. The product is a complete asynchronous workflow: **watch public source → extract and ground evidence → update long-term state → detect a change → plan a bounded inquiry → await human approval → assemble a research artifact and audit trail.**

Milwaukee is the stronger choice if the team can speak authentically about the local stakes, identify a real community partner or reporting audience, and tell a story that a distant competitor cannot. San Francisco remains a good data-rich fallback, but it is less defensible as *your* insight.

## References

[1]: https://biglocalnews.org/content/news/2023/06/23/welcome-to-agenda-watch.html "Big Local News — Welcome to Agenda Watch"

[2]: https://data.milwaukee.gov/ "City of Milwaukee Open Data Portal"

[3]: https://milwaukee.legistar.com/Calendar.aspx "City of Milwaukee — Legistar calendar"

[4]: https://milwaukeecounty.legistar.com/Calendar.aspx "Milwaukee County — Legistar calendar"

[5]: https://data.county.milwaukee.gov/ "Milwaukee County Open Data Portal"

[6]: https://stories.opengov.com/milwaukee/published/T2SmXmV8p "City of Milwaukee — Open Checkbook"
