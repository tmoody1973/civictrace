# CivicTrace UX Copy Guide — plain English for journalists, citizens, and advocacy groups

**Who reads our screens:** a beat reporter on deadline, a neighborhood advocate after work,
a citizen who has never seen a Legistar file. None of them know our system's words.
**The bar: a first-time reader understands every screen without being taught.**
Requested by Tarik 2026-08-21; every new screen and MOO-724 (the /impeccable overhaul)
must follow this guide.

## The rules

1. **8th-grade reading level.** Short sentences. One idea per sentence. If a sentence needs
   a comma and an "and," it is probably two sentences.
2. **Say what the reader gets or what happens next** — not what the system is.
   - ✗ "Candidate bundle assembled from Legistar matter metadata"
   - ✓ "Here is what the City's official record lists for this file."
3. **Every button states its consequence.** "Approve — create this case," never just "Submit."
   If an action is irreversible or leaves the system, the words say so before the click.
4. **Jargon gets defined the first time, in the same breath, in one clause.**
   "its fingerprint (a code that changes if even one byte of the file changes)."
   If a term needs a paragraph to define, don't use the term.
5. **Uncertainty in words, never in codes.** "The 2025 report has not been published yet" —
   the enum value `NOT_PUBLISHED` may appear as a badge, but the sentence next to it carries
   the meaning.
6. **Never blame the reader; always give the way forward.** "That file number wasn't found in
   the City's record system. Check the number on the City's website, or try a different one."
7. **Honesty over reassurance.** If the system doesn't know, the screen says it doesn't know.
   Trust language ("verified," "matches") appears only when code actually checked.
8. **Questions make better labels than nouns.** "Which document states the promise?" beats
   "Attachment role assignment."

## Vocabulary — system word → screen words

| Our system says | The screen says |
|---|---|
| artifact | document, record, or recording |
| content hash | fingerprint (a code that changes if the file changes) |
| Decision Delta | what changed |
| evidence anchor | where in the record (page 5 / 1:39:40 in the meeting) |
| original_commitment | the promise — what the City committed to |
| later_evidence | what happened after — follow-through or review |
| Decision Delta staged | a change is ready for your review |
| NOT_PUBLISHED | not published yet (and what we expect, and since when) |
| diarization label | "Speaker 1" — a label from the audio, not a verified name |
| ledger / ledger events | the case record / everything the system did, in order |
| manifest | the case recipe: which documents, from where, with which fingerprints |
| corpus | (never say it) |
| provenance | where this came from and when we saved it |
| approval token | your signed approval (it expires and is recorded) |
| inquiry packet | the draft questions — nothing is sent without you |

## The three sentences every major screen must answer

1. **What am I looking at?** (one plain sentence at the top)
2. **What should I do?** (numbered if more than one step)
3. **What happens when I do it?** (consequence, cost in time, and what I can undo)

## Litmus tests before shipping copy

- Read it aloud. If you stumble, rewrite.
- Would a smart neighbor with no civic-tech background do the right thing on first try?
- Delete every sentence and see which ones the screen actually needs. Ship only those.
- Does any word on the screen exist only because the codebase uses it? Translate it.
