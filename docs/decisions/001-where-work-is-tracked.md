# 001 — Where work is tracked (Linear + local markdown + GitHub later)

- **Decision** — Planned build work lives in Linear (team Moodyco); quick scratch notes live in `.scratch/` files; GitHub Issues turns on only once the repo has a GitHub remote.
- **Why this came up** — On 2026-08-19 we wired the mattpocock engineering skills into CivicTrace. Those skills need one answer to "where do issues go?" or they guess. Getting it wrong means tickets scattered across tools during a hackathon with a fixed deadline.
- **Options**
  1. *GitHub Issues only* — keeps code and tickets together, but the repo had no `.git` and no remote yet, so nothing could be filed on day one.
  2. *Local markdown only* — zero setup, but no dependency links, no status board, and no history once files are deleted.
  3. *Linear primary + local scratch + GitHub later* — Linear already holds every other Moodyco project and has the issue-as-spec habit (Intent / Acceptance / Verification); markdown covers throwaway notes; GitHub is a one-line switch later.
- **What we chose and why** — Option 3. Joint call (Tarik asked for "both", then added Linear). Linear is where Tarik already plans; the skills can call its MCP tools directly.
- **What we gave up** — Three places to look instead of one. A public contributor can't see Linear. We accept that because there are no external contributors during the hackathon.
- **How we'll know if this was right** — At submission time, every shipped slice has a Linear issue with a verification comment, and nobody had to hunt for "where is that ticket".
- **What actually happened** — _(Tarik fills this in later.)_
