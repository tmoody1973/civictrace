import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TranscriptPane } from "@/features/artifact/transcript-pane";
import type { TranscriptView } from "@/lib/api-types";

const transcript: TranscriptView = {
  transcript_id: "tr-test",
  artifact_id: "znd-committee-2026-07-28",
  segment_start_seconds: 5287,
  segment_end_seconds: 5990,
  stt_provider: "google-speech-v2",
  stt_model: "chirp_3",
  diarization: true,
  confidence_note: "The transcription model reports no per-word confidence; verify against the recording.",
  segments: [
    { start_ms: 0, end_ms: 13_840, speaker_label: "SPEAKER_0", text: "approving amendment number one", confidence: null },
    {
      start_ms: 693_120,
      end_ms: 696_360,
      speaker_label: "SPEAKER_0",
      text: "Hearing none. Alderwoman Cox moves to recommend adoption.",
      confidence: null,
    },
  ],
};

describe("TranscriptPane", () => {
  it("shows segments with meeting-absolute time and speaker labels as labels", () => {
    render(<TranscriptPane transcript={transcript} anchoredSpan={null} />);
    expect(screen.getByText("1:28:07")).toBeInTheDocument(); // 5287s + 0ms
    expect(screen.getByText("1:39:40")).toBeInTheDocument(); // the committee-action moment
    expect(screen.getAllByText("Speaker 0")).toHaveLength(2);
    expect(screen.queryByTestId("transcript-segment-highlighted")).toBeNull();
  });

  it("highlights the cited evidence span and never hides the confidence gap", () => {
    render(<TranscriptPane transcript={transcript} anchoredSpan={{ startMs: 693_120, endMs: 696_360 }} />);
    const highlighted = screen.getByTestId("transcript-segment-highlighted");
    expect(highlighted).toHaveTextContent("Alderwoman Cox moves to recommend adoption");
    expect(highlighted).toHaveAttribute("aria-current", "true");
    expect(screen.getByText("Cited evidence span")).toBeInTheDocument();
    expect(screen.getByText("Confidence not reported")).toBeInTheDocument();
  });
});
