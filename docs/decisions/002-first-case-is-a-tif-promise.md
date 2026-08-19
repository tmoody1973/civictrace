# 002 — The first case follows a TIF promise, with a missing-record check inside it

- **Decision** — The Slice 1 demo case follows one City of Milwaukee Tax Incremental District (TID) file: the Council approval (the Promise) and a later file for the same district (amendment, extension, or annual report). Inside that same case we include one expected-but-absent record (a report-back or unpublished attachment) so the system must say `NOT_PUBLISHED` on screen.
- **Why this came up** — 2026-08-19. The fixture issue (MOO-685) needs one real case. Three promise types were on the table and they pull the build in different directions. Picking wrong means either a boring demo or a build that breaks on stage.
- **Options**
  1. *TIF promise* — money, a place, a before/after. Tables anchor well. Risk: a judge expects an accusation; we must show restraint.
  2. *Report-back promise* — "did the report land by the date?" Cleanest evidence (present/absent/dated). Lowest build risk. Can look thin.
  3. *Capital project promise* — a thing on your block. Needs matching one project across years of budget PDFs, which is entity linking we do not build in Slice 1.
- **What we chose and why** — Option 1 with option 2's mechanic inside it. Tarik's call, Claude recommended. One case gives the rich story and the honest "we do not know" in the same screen, with no extra code.
- **What we gave up** — The safest build (option 2 alone). And the neighborhood-level story (option 3) waits for a later slice.
- **How we'll know if this was right** — During MOO-685 we find two real Legistar PDFs for one TID whose key numbers sit in tables we can anchor by page, plus one honest missing record. If the PDFs are too messy to anchor by hand in an afternoon, we switch to option 2 (same code, smaller story) and note it here.
- **What actually happened** — _(Tarik fills this in later.)_
