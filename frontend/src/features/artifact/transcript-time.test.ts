import { describe, expect, it } from "vitest";

import { meetingTime, segmentOverlapsSpan, speakerLabelText } from "@/features/artifact/transcript-time";
import type { TranscriptSegmentView } from "@/lib/api-types";

const segment = (start_ms: number, end_ms: number): TranscriptSegmentView => ({
  start_ms,
  end_ms,
  speaker_label: "SPEAKER_0",
  text: "words",
  confidence: null,
});

describe("meetingTime", () => {
  it("shows the committee-action moment at the official player's clock", () => {
    // 693120 ms into the segment that starts 5287s into the recording = 1:39:40
    expect(meetingTime(5287, 693_120)).toBe("1:39:40");
  });

  it("pads minutes and seconds", () => {
    expect(meetingTime(0, 0)).toBe("0:00:00");
    expect(meetingTime(3661, 0)).toBe("1:01:01");
  });
});

describe("segmentOverlapsSpan", () => {
  it("matches segments inside the cited span and rejects the rest", () => {
    const span = { startMs: 693_120, endMs: 696_360 };
    expect(segmentOverlapsSpan(segment(693_120, 696_360), span)).toBe(true);
    expect(segmentOverlapsSpan(segment(690_000, 694_000), span)).toBe(true);
    expect(segmentOverlapsSpan(segment(0, 10_000), span)).toBe(false);
    expect(segmentOverlapsSpan(segment(0, 10_000), null)).toBe(false);
  });
});

describe("speakerLabelText", () => {
  it("keeps the label a label", () => {
    expect(speakerLabelText("SPEAKER_2")).toBe("Speaker 2");
    expect(speakerLabelText("unknown")).toBe("unknown");
  });
});
