// Time math for the transcript pane. Segment times are ms relative to the transcribed
// focus segment; the UI shows meeting-absolute time so it matches the official player.

import type { TranscriptSegmentView } from "@/lib/api-types";
import type { TranscriptSpan } from "@/features/trace/artifact-jump";

export function meetingTime(segmentStartSeconds: number, relativeMs: number): string {
  const totalSeconds = segmentStartSeconds + Math.floor(relativeMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${hours}:${pad(minutes)}:${pad(seconds)}`;
}

export function segmentOverlapsSpan(segment: TranscriptSegmentView, span: TranscriptSpan | null): boolean {
  if (!span) return false;
  return segment.start_ms < span.endMs && segment.end_ms > span.startMs;
}

/** "SPEAKER_1" → "Speaker 1" — friendlier text, still visibly a label, never a name. */
export function speakerLabelText(rawLabel: string): string {
  const match = /^SPEAKER_(\d+)$/.exec(rawLabel);
  return match ? `Speaker ${match[1]}` : rawLabel;
}
