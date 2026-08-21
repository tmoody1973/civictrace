"use client";

import { Info } from "lucide-react";
import { useEffect, useRef } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  meetingTime,
  segmentOverlapsSpan,
  speakerLabelText,
} from "@/features/artifact/transcript-time";
import type { TranscriptSpan } from "@/features/trace/artifact-jump";
import type { TranscriptSegmentView, TranscriptView } from "@/lib/api-types";

const LOW_CONFIDENCE_BELOW = 0.7;

/** The meeting record as text: every segment timestamped, every speaker a label. */
export function TranscriptPane({
  transcript,
  anchoredSpan,
}: {
  transcript: TranscriptView;
  anchoredSpan: TranscriptSpan | null;
}) {
  const highlightRef = useRef<HTMLLIElement | null>(null);

  useEffect(() => {
    highlightRef.current?.scrollIntoView?.({ block: "center" });
  }, [anchoredSpan]);

  const start = meetingTime(transcript.segment_start_seconds, 0);
  const end = meetingTime(transcript.segment_end_seconds, 0);
  const firstHighlightedIndex = transcript.segments.findIndex((segment) =>
    segmentOverlapsSpan(segment, anchoredSpan),
  );

  return (
    <div className="flex h-full min-h-0 flex-col gap-3" data-testid="transcript-pane">
      <p className="text-sm text-muted-foreground">
        Meeting transcript · {start}–{end} of the recording · {transcript.stt_model} (
        {transcript.stt_provider}), diarization {transcript.diarization ? "on" : "off"}. Speaker
        numbers are diarization labels, not verified identities.
      </p>
      <Alert>
        <Info aria-hidden="true" />
        <AlertTitle>Confidence not reported</AlertTitle>
        <AlertDescription>{transcript.confidence_note}</AlertDescription>
      </Alert>
      <ScrollArea className="min-h-0 flex-1 rounded-md border">
        <ul className="divide-y" aria-label="Transcript segments">
          {transcript.segments.map((segment, index) => (
            <TranscriptSegmentRow
              key={segment.start_ms}
              segment={segment}
              segmentStartSeconds={transcript.segment_start_seconds}
              highlighted={segmentOverlapsSpan(segment, anchoredSpan)}
              ref={index === firstHighlightedIndex ? highlightRef : null}
            />
          ))}
        </ul>
      </ScrollArea>
    </div>
  );
}

function TranscriptSegmentRow({
  segment,
  segmentStartSeconds,
  highlighted,
  ref,
}: {
  segment: TranscriptSegmentView;
  segmentStartSeconds: number;
  highlighted: boolean;
  ref: React.Ref<HTMLLIElement> | null;
}) {
  const lowConfidence = segment.confidence !== null && segment.confidence < LOW_CONFIDENCE_BELOW;
  return (
    <li
      ref={ref}
      aria-current={highlighted ? "true" : undefined}
      data-testid={highlighted ? "transcript-segment-highlighted" : "transcript-segment"}
      className={`space-y-1 p-3 text-sm ${highlighted ? "bg-accent ring-2 ring-inset ring-ring" : ""}`}
    >
      <p className="flex flex-wrap items-center gap-2">
        <span className={`font-mono text-xs ${highlighted ? "text-foreground" : "text-muted-foreground"}`}>
          {meetingTime(segmentStartSeconds, segment.start_ms)}
        </span>
        <Badge variant="outline" title="Diarization label, not a verified identity">
          {speakerLabelText(segment.speaker_label)}
        </Badge>
        {highlighted ? <Badge>Cited evidence span</Badge> : null}
        {lowConfidence ? <Badge variant="destructive">Low confidence</Badge> : null}
      </p>
      <p>{segment.text}</p>
    </li>
  );
}
