# CivicTrace Pitch Deck Update — Evidence Trace UX

## Slide 6 — Replace with: Every AI conclusion has an Evidence Trace

**Title:** Every AI conclusion has an Evidence Trace

**Subhead:** The editor sees the verifiable workflow—not hidden model reasoning.

| Workflow step | What the editor can inspect |
|---|---|
| Source preserved | Canonical URL, artifact hash, retrieval time |
| Evidence extracted | Exact PDF page, dataset row, or meeting timestamp |
| Case evaluated | Source-supported entity/project connection |
| Later record compared | Original commitment beside later evidence |
| Policy checks passed | Anchor, privacy, and scope validation outcome |
| Human decision required | The proposed inquiry and the approval boundary |

**Footer statement:**

> Collapsed by default. Every step opens the original evidence. The model’s private reasoning never becomes the product record.

## Slide 9 — Replace with: One orchestrator. Eight bounded agents.

**Title:** One orchestrator. Eight bounded agents.

**Left-side agent roster:**

| Agent | Output |
|---|---|
| Document / Media Evidence | Anchored public facts |
| Entity Resolution / Case Linker | Conservative case-link proposals |
| Delta Investigator | Original-versus-later Decision Delta |
| Quality Reviewer | Pass, revise, or block decision |
| Inquiry Planner / Brief Builder | Draft-only artifact |

**Right-side orchestrator rules:**

1. Routes the smallest permissible workflow.
2. Owns queues, retries, idempotency, state transitions, and validation.
3. Gives agents read-only bounded evidence—not open web/database/publishing access.
4. Stages a case only after deterministic checks and reviewer policy review.

**Footer statement:**

> Agents reason over evidence. The orchestrator enforces the rules. A human authorizes every external-facing action.

## Slide 12 — Add one Multimodal UX proof point

**Replace the Best Multimodal UX proof with:**

> Synchronized document, table, transcript/video, timeline, map context, and a collapsible **Evidence Trace** that links each system step to its source anchor and validation state.

## Slide 13 — Add demo beat after Decision Delta opens

**New beat between steps 3 and 4:**

> The reviewer expands the collapsed Evidence Trace, opens the original PDF and later record directly from two trace steps, and confirms that the system has preserved an explicit unknown.

## Speaker note — How to explain it to judges

> “We do not ask judges to trust a chain-of-thought. We show an Evidence Trace: a deterministic audit trail of the source artifact, agent proposal, source anchors, validators, and required human decision. Every visible conclusion can be opened against the original public record.”

## Reference

[1]: https://elements.ai-sdk.dev/components/chain-of-thought "AI SDK Elements — Chain of Thought"
