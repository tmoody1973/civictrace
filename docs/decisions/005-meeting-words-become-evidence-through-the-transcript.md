# 005 — Meeting words become evidence through the transcript, not the video

**Date:** 2026-08-21 · **Issue:** MOO-717

## Decision

The AI never touches the 2.9GB meeting video. It reads only the small, committed transcript
(the diarized text of the 12-minute agenda item), in bounded slices, and every claim it makes
must carry an exact millisecond timestamp range where those words were actually said.

## Why this came up

We wanted the case file to quote the hearing — "the developer said construction starts this
fall" — with a receipt. The raw material is a 3-hour, 2.9GB video. Feeding video to a model is
slow, expensive, and unverifiable. If we got this wrong, the system could "quote" words nobody
said, or name a speaker the record never named.

## Options

1. **Send video (or audio) to a multimodal model.** Richest input, but costly per run, and we
   cannot mechanically check what the model claims it heard.
2. **Send the whole transcript in one prompt.** Cheap enough here, but it breaks our standing
   rule that agents get bounded slices, and it doesn't scale past one meeting.
3. **A read-only transcript-slice tool + a code gate that re-checks every quote.** The model
   asks for slices (max 5 minutes of speech each), and validation code refuses any evidence
   whose quoted words are not literally present in the timestamped slice it cites.

## What we chose and why

Option 3 (joint: the pattern was already proven for PDF pages in slice 2; Claude extended it
to transcripts). It keeps three properties we refuse to lose: cost stays flat (~$0.01 of model
spend for the whole meeting step), every quote is mechanically verifiable against the record,
and a speaker label like SPEAKER_2 can never silently become a person's name — the gate
rejects a name in the label field because a name is not a label the transcript contains.

Two supporting choices, same spirit:

- **The cloud never re-downloads the video.** It was hash-verified once when a human vaulted
  it. Re-reading 2.9GB per run adds cost, not information. Files over 64MB skip the per-run
  re-hash; the vault only confirms the object still exists.
- **Discussion is not a decision.** Evidence may only be labeled a DECISION or VOTE when the
  cited slice itself contains committee-action words (motion, second, so ordered…). A
  presentation stays a claim.

## What we gave up

The model never hears tone, sees slides, or catches words the transcription missed. If the
speech-to-text step erred, the error carries through — our anchor proves "the transcript says
this at 11:33," not "this is exactly what was said." Also, the >64MB no-re-hash rule means a
corrupted vault video would not be caught by the replay itself, only by the recorded hash at
next manual verification.

## How we'll know if this was right

The live run: the Delta Investigator's staged update cites three hearing moments with exact
timestamp ranges, and the validation gate rejected nothing invented (0 retries, 0 rejections).
If a future meeting produces evidence the gate rejects for phantom quotes, the design is doing
its job; if it *accepts* a quote a human can't find at that timestamp, the design failed.

## What actually happened

_(Tarik fills this in.)_
