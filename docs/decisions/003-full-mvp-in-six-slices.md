# 003 — Build the full PRD MVP, in six vertical slices

- **Decision** — We ship the complete hackathon MVP defined in `CLAUDE.md` §8 / the PRD, delivered as six vertical slices; each slice is a whole, working, tested piece — never a thinner version of the product.
- **Why this came up** — 2026-08-19, after Slice 1 shipped. Tarik asked, in plain words, whether slicing meant a half-product. It must not. Slicing is about order and proof, not about cutting scope.
- **Options**
  1. *Build everything at once, then test.* Fastest-looking. In practice nothing is provable until the end, and a hackathon deadline turns that into a mock demo.
  2. *Build a thin demo path only (hard-coded delta, fake agent, pretty UI).* Quick to show. Fails the hackathon's own acceptance tests (idempotent replay, grounding, approval boundary) and our rules.
  3. *Six vertical slices, each fully real for its part.* Slower to a first screenshot; every slice is demo-able on its own and each builds on proven pieces.
- **What we chose and why** — Option 3. Tarik's call, Claude recommended. The roadmap: (1) evidence spine ✅ → (2) real Gemini Flash agent + Decision Delta + Quality Review → (3) Evidence Studio UI → (4) human approval token + inquiry packet + failed-approval demo → (5) Cloud Run / Firestore / GCS / Pub-Sub / Tasks / BigQuery deploy, IaC, trace lineage, teardown → (6) meeting media (Speech-to-Text V2 + Media Evidence Agent), which the PRD itself places after the City loop passes. Out of scope stays exactly what `CLAUDE.md` §1 already excludes (MPS live monitoring, County, TinyFish/Parallel, email/CMS, autonomous outreach).
- **What we gave up** — The first full-stack screenshot arrives later than with option 2. Cloud deploy (Slice 5) sits late, which is a schedule risk we accept because it needs plan-mode gates and real money; we will start Slice 5's human-owned GCP setup early (MOO-690 already does the first part).
- **How we'll know if this was right** — Each slice closes with its Linear verification comment and a real run; by Slice 4 the four-minute demo script in `docs/hackathon/demo-and-repo-plan.md` can be recorded locally end to end; Slice 5 adds the Console proof without changing product behaviour.
- **What actually happened** — _(Tarik fills this in later.)_
