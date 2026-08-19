# CivicTrace API Stack and Vendor Recommendation

## Executive Decision

CivicTrace should be built with a **small, Google Cloud-centered core** and direct adapters to the authoritative Milwaukee/MPS sources. **Do not make TinyFish or Parallel AI dependencies for the hackathon MVP.** Both can add value later, but only as narrowly scoped **research/discovery or resilient extraction adapters**, never as the system of record or evidence authority.

> **Evidence rule:** CivicTrace must preserve and cite the original City, County, MPS, or state source. A third-party research/extraction response can help discover or parse a page, but it cannot become the only evidence behind a Decision Delta.

| Vendor | Hackathon MVP | Pilot / expansion | Best CivicTrace role |
|---|---|---|---|
| **TinyFish** | **No-go as a dependency.** | **Conditional.** Evaluate its Fetch API only for a specifically documented, public, dynamic/fragile source adapter that direct retrieval cannot handle. | Known-URL fetch/extraction fallback; never the primary evidence vault. |
| **Parallel AI** | **No-go as a dependency.** | **Conditional go.** Strong candidate for an editor-facing *source discovery / lead research* feature across new jurisdictions. | Find candidate official sources or extract a difficult public page; never generate a case conclusion from web research alone. |

---

## 1. The Minimum Viable API Stack

### 1.1 Required P0 services and interfaces

| Layer | API / service | Why CivicTrace needs it | Interface / credential | MVP decision |
|---|---|---|---|---|
| **AI reasoning** | Gemini API through Vertex AI or Gemini API | Structured extraction, grounded comparison, case linking, Decision Delta proposals, and brief drafts. | Google project/service identity or Gemini API key, depending on chosen integration. | **Required by hackathon.** |
| **Agent framework** | Google ADK | Defines specialized typed agents and tool boundaries. | Application dependency, not a separate paid SaaS API. | **Required by hackathon.** |
| **Meeting transcription** | Google Cloud Speech-to-Text V2 batch recognition | Long-running, timestamped City/MPS public-meeting transcripts; optionally diarized speaker labels. | Google service identity; Cloud Storage URI. | **P1 for media monitor; P0 only if video/audio is in the demo.** |
| **Public meeting data** | Milwaukee Legistar Web API | City Council/committee event, item, agenda/minutes, and public file metadata. | Public API; adapter with source fingerprinting and rate limits. | **P0.** |
| **Public City data** | City of Milwaukee CKAN API | Property, address, geography, service, and selected structured evidence. | Public API. | **P0.** |
| **Source artifact vault** | Google Cloud Storage | Immutable raw source snapshots, retrieved documents, transcripts, and generated packets. | Google service identity. | **P0.** |
| **Durable work queue** | Pub/Sub + Cloud Tasks | Source-change fan-out, idempotent asynchronous workers, retries, and bounded concurrency. | Google service identity. | **P0.** |
| **Case/evidence state** | Firestore | Case state, evidence ledger, jobs, approvals, corrections, and graph edges. | Google service identity. | **P0.** |
| **Large structured corpus** | BigQuery | Historical data/backfills, partitioned structured records, prefiltering before model calls. | Google service identity. | **P0 for “heavy lifting” proof; can start with a small dataset.** |
| **Application runtime** | Cloud Run | API, UI/backend, source watcher, and worker services with scale to zero. | Cloud Run IAM/service identity. | **P0.** |
| **Source scheduling** | Cloud Scheduler | Checks sources with no event/webhook feed. | Google service identity. | **P0 for recurring monitor; schedule can be disabled in a replay-only demo.** |
| **Observability** | Cloud Logging + Cloud Trace | Job lineage, agent versions, retries, failure state, and demo proof. | Google service identity. | **P0.** |
| **Secrets / identity** | Secret Manager + IAM | Third-party keys, service identity, least privilege, and secure endpoint configuration. | IAM / project config. | **P0.** |

### 1.2 Direct public-source adapters

CivicTrace should call the source closest to the original public record. These are adapters, not generic “scrapers.” Each adapter must preserve the canonical URL, source-specific ID, retrieval timestamp, content hash, terms/access note, and source version/fingerprint.

| Source | Primary CivicTrace use | Integration approach | MVP status |
|---|---|---|---|
| **Milwaukee City Legistar** | Council/committee agendas, meeting metadata, items, official files, final minutes/video status. | Direct public Web API / public document URLs. Poll by updated event/file metadata; use stable external IDs and content hash. [1] | **P0.** |
| **Milwaukee City Open Data (CKAN)** | Geographic/place context and selected public dataset evidence. | CKAN API/catalog and source-specific data endpoints; land selected tables in BigQuery. [2] | **P0.** |
| **City Open Checkbook** | Seeded, corroborating spending/vendor source when record is public and stable. | Treat as curated export or known source, not a critical live dependency until formal export/API behavior is verified. [3] | **P1.** |
| **MPS Board / IC Board / E-Notify** | Agendas, public meeting information, public recordings/proceedings, notices. | Separate source adapter. Do not assume City Legistar covers MPS. Preserve public source URL and media artifact metadata. [4] | **P1 demo extension.** |
| **MPS improvement/report-card pages** | Public plan and aggregate institution-level outcome/progress evidence. | Direct official page/document retrieval only. | **P1 demo extension.** |
| **MPS bids/RFPs** | Public procurement/implementation artifact where lawfully available. | Use only published award/contract/tabulation material; do not depend on dynamic vendor submission workflow. [5] | **P2.** |
| **Milwaukee County sources** | Context for cross-jurisdictional projects. | Separate County Legistar/portal adapter after City core works. [6] | **P2.** |

### 1.3 Application and user-access APIs

| Capability | Recommendation | Why |
|---|---|---|
| **User authentication / roles** | Start with Firebase Authentication or Identity Platform for editor/reviewer identity; use Cloud Run IAM for internal services. | Approval events must identify a real reviewer and role. Do not expose worker endpoints directly to browser clients. |
| **Maps** | Start with MapLibre/Leaflet plus a permitted base-map source and City public GIS/CKAN geometry. | The product needs a place canvas, not a costly routing/geocoding platform. Add Google Maps only if a later UX requirement actually needs it. |
| **Email / CMS / newsletter** | None in MVP. Render a draft in CivicTrace first. | Prevents accidental external communication and avoids integration work that does not improve the core evidence loop. |
| **Public-records request service** | None in MVP. Export a human-approved outline/packet. | CivicTrace proposes a bounded question; a person chooses the legal/process channel. |
| **Webhooks** | Receive only from authorized internal Google services or a specifically approved third-party vendor. | Verify signatures, bind to an event ID, and enqueue work rather than process synchronously. |

---

## 2. What You Do *Not* Need Yet

Do not add a vector database, full graph database, browser automation vendor, CMS integration, email API, generic web crawler, paid mapping platform, separate data warehouse beyond BigQuery, or an external workflow tool simply because the architecture looks sophisticated. The hackathon proof is stronger when one direct, official-source path is reliable and explainable.

A simple, correct state model—Firestore case ledger plus BigQuery for large structured rows—is sufficient for the MVP. If semantic retrieval becomes necessary, first evaluate Vertex AI embeddings with BigQuery/vector search or a managed serverless option. Do not introduce an always-on database cluster solely to claim “agent memory.”

---

## 3. TinyFish Evaluation

### 3.1 Verified capability

TinyFish exposes four API surfaces: **Search**, **Fetch**, **Agent**, and **Browser**. Its Fetch API accepts known URLs, returns clean HTML/Markdown/JSON, supports up to ten URLs in one request, supports cache TTL and conditional validators, can scope extraction with CSS selectors, and supports PDF text extraction. Its documentation says images and video are binary content types that return an error, so it is not a meeting-media ingest service. [7] TinyFish’s Agent API can follow a natural-language goal on a real web site, offers structured output, and supports synchronous, asynchronous, or server-sent-event run modes. [8]

### 3.2 Where TinyFish could help

TinyFish has a narrow future role: a **fallback fetch adapter for a known, public, JavaScript-heavy or format-unstable official page**, provided direct retrieval cannot reliably extract the needed public content. Its conditional requests and fetch freshness controls can help reduce redundant parsing. Use it only after an adapter test demonstrates a direct source limitation.

### 3.3 Why TinyFish should not be in the MVP critical path

The CivicTrace MVP begins with known official sources—Legistar, CKAN, and curated public documents. Those sources should be retrieved directly and stored as immutable artifacts. An autonomous browser agent adds cost, non-determinism, potential source-access/terms complexity, and a weaker provenance story. TinyFish’s own documentation distinguishes Fetch from Agent/Browser and notes that Agent/Browser consume wallet balance, while Search/Fetch are free at any balance. [9]

Do not use TinyFish Agent or Browser to issue public-records requests, sign in to a source system, bypass friction/anti-bot measures, submit forms, or perform user-facing actions. Do not treat its structured response as an authoritative source; always store/cite the public canonical URL and retrieved original artifact.

### 3.4 TinyFish decision

| Stage | Decision | Rule |
|---|---|---|
| **Hackathon MVP** | **No-go** | Build direct adapters; do not spend time integrating a generic browser agent. |
| **MPS demo extension** | **No-go by default** | Use public MPS source/media URLs and Google transcription. |
| **Pilot** | **Conditional** | Use only as an adapter fallback for one documented public page where direct HTTP/official API extraction fails. |
| **Product expansion** | **Evaluate** | Could reduce adapter maintenance for dynamic sites, but cache/raw artifact/provenance and terms controls remain mandatory. |

---

## 4. Parallel AI Evaluation

### 4.1 Verified capability

Parallel’s **Extract API** converts public URLs—including JavaScript-heavy pages and PDFs—into clean Markdown, returning relevant excerpts or full content. The response includes the source URL, title, possible publish date, excerpts, and optional full content. [10] Parallel also documents Search, Task, FindAll, and Monitor. Its Task API is designed for multi-hop research with cited structured output; Monitor is positioned for scheduled query/change tracking with webhook notification. [11]

Parallel additionally provides a Source Policy for Search and Task that can allow or exclude domains and apply a date constraint. The official documentation warns that narrow source policies can reduce result quality and supports up to 200 included/excluded domains per request. [12]

### 4.2 Where Parallel could add real value

Parallel can add value as an **editor-initiated research companion** after the MVP. Consider two bounded uses:

1. **Source discovery before a case is opened.** A reporter can ask: “Find official Milwaukee/MPS sources published since a specific date about a named project.” Parallel Search/Task can return candidate URLs, which CivicTrace then verifies and ingests directly through its own source/admission process.
2. **Cross-jurisdiction expansion.** When CivicTrace moves beyond Milwaukee, Parallel Extract may reduce initial research friction for a new city’s poorly documented or JavaScript-heavy public pages. Parallel Monitor might help identify a change across a bounded set of official domains, but it should trigger a CivicTrace verification job—not directly update case state.

Use `include_domains` to constrain research to appropriate official domains when the task requires a high-assurance corpus, such as `milwaukee.gov`, `milwaukeecounty.gov`, `milwaukeepublicschools.org`, `wi.gov`, and the relevant meeting platform domain. Even then, preserve the original response and conduct CivicTrace’s own evidence/anchor validation.

### 4.3 Why Parallel should not power the MVP source monitor

CivicTrace needs durable, deterministic coverage of defined sources and must explain precisely why a record was processed. Parallel’s research abstraction is valuable for discovery but is not a substitute for a direct source adapter, immutable artifact vault, source-specific ID/fingerprint, and exact page/timestamp/row anchor. Its web-research output should never be the sole basis for a Decision Delta, a named entity link, or an inquiry artifact.

### 4.4 Parallel decision

| Stage | Decision | Rule |
|---|---|---|
| **Hackathon MVP** | **No-go as a dependency** | Do not add external research latency/cost when direct official sources prove the core workflow. |
| **Hackathon bonus / optional demo** | **Conditional** | A short, clearly labeled “Find official sources” editor tool can be impressive only after the core demo works; it must feed a verification queue. |
| **Pilot** | **Conditional go** | Evaluate Search/Extract/Task for editor-led discovery and new-city research. Keep its role read-only and source-policy bounded. |
| **Product expansion** | **Likely useful** | Useful for jurisdiction onboarding and low-frequency research; measure cost/quality versus direct adapters before production commitment. |

---

## 5. Recommended API Boundaries

### 5.1 Source-adapter interface

Every direct or vendor-assisted source adapter must implement the same internal contract.

```typescript
interface PublicSourceAdapter {
  sourceId: string;
  jurisdiction: "milwaukee_city" | "mps" | "milwaukee_county";
  allowedDomains: string[];
  discover(cursor?: string): Promise<SourceEvent[]>;
  fetchCanonical(event: SourceEvent): Promise<RawArtifact | SourceUnavailable>;
  fingerprint(artifact: RawArtifact): Promise<string>;
  provenance(artifact: RawArtifact): ProvenanceRecord;
}
```

Third-party services may assist `discover` or `fetchCanonical` only when the adapter still returns a canonical original-source URL and allows CivicTrace to preserve the raw response, content hash, retrieval time, and source metadata.

### 5.2 Research-discovery interface

Keep vendor research separate from authoritative ingestion.

```typescript
interface ResearchDiscoveryProvider {
  findCandidateSources(query: string, policy: SourcePolicy): Promise<ResearchCandidate[]>;
}

interface ResearchCandidate {
  url: string;
  title?: string;
  excerpt?: string;
  discoveryProvider: "parallel" | "tinyfish" | "manual";
  discoveredAt: string;
  requiresCanonicalVerification: true;
}
```

A candidate source enters CivicTrace only after the Source Sentinel independently retrieves it through an approved adapter and validates source policy/provenance.

### 5.3 Media interface

Neither TinyFish nor Parallel should be used for public meeting-media ingestion. Use the public recording URL, Cloud Storage preservation, and Google Cloud Speech-to-Text batch recognition. Store diarized speaker labels as segmentation metadata, not identity.

---

## 6. API Key and Secret Inventory

| Secret / identity | Needed in MVP? | Storage | Notes |
|---|---:|---|---|
| Google Cloud runtime service account | Yes | IAM, not an application secret file | Use least privilege and workload identity where available. |
| Gemini / Vertex AI access | Yes | Service identity or Secret Manager depending on integration | Do not expose to browser. |
| Firebase/Identity config | Conditional | Public client config plus server-side IAM/Secret Manager as appropriate | Needed once editor approvals are multi-user. |
| TinyFish API key | No | Secret Manager only if future adapter enabled | Never put in client/UI or repository. |
| Parallel API key | No | Secret Manager only if future research feature enabled | Never put in client/UI or repository. |
| CMS/email integration key | No | Secret Manager, later only | Exclude from MVP. |

---

## 7. Build Order

1. Implement Milwaukee Legistar adapter with direct public retrieval and artifact hashing.
2. Implement selected CKAN dataset adapter and load a small, real dataset to BigQuery.
3. Add Cloud Storage, Firestore, Pub/Sub, Cloud Tasks, Gemini/ADK extraction, and a source-grounded Decision Delta.
4. Add Cloud Run deployment, Cloud Scheduler, observability, IAM, and approval gate.
5. Add public meeting audio → Cloud Storage → Speech-to-Text → Media Evidence Agent only after the document loop works.
6. Add MPS as a second direct adapter after the City demonstration is stable.
7. Evaluate Parallel for editor-led discovery after the MVP; evaluate TinyFish only after a documented direct-adapter failure.

This ordering gives the best Taskmaster and architectural-design story: the product reliably owns the public-evidence loop before it uses a general-purpose AI web layer.

---

## References

[1]: https://milwaukee.legistar.com/Calendar.aspx "City of Milwaukee — Legistar calendar"

[2]: https://data.milwaukee.gov/ "City of Milwaukee Open Data Portal"

[3]: https://stories.opengov.com/milwaukee/published/T2SmXmV8p "City of Milwaukee — Open Checkbook"

[4]: https://www.milwaukeepublicschools.org/about/board "Milwaukee Public Schools — Board of School Directors"

[5]: https://www.milwaukeepublicschools.org/about/directory/finance/procurement-risk-management/vendors/bids-rfps "Milwaukee Public Schools — Bids and RFPs"

[6]: https://milwaukeecounty.legistar.com/Calendar.aspx "Milwaukee County — Legistar calendar"

[7]: https://docs.tinyfish.ai/fetch-api "TinyFish — Fetch API"

[8]: https://docs.tinyfish.ai/agent-api "TinyFish — Agent API"

[9]: https://docs.tinyfish.ai/ "TinyFish Developer Documentation"

[10]: https://docs.parallel.ai/extract/extract-quickstart "Parallel — Extract API Quickstart"

[11]: https://docs.parallel.ai/getting-started/overview "Parallel API Overview"

[12]: https://docs.parallel.ai/resources/source-policy "Parallel — Source Policy"
