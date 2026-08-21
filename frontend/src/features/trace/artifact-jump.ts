// Bridge from any anchor (trace row, delta chip) to the PDF pane (MOO-699 listens).

export const ARTIFACT_JUMP_EVENT = "civictrace:jump-artifact";

export type TranscriptSpan = { startMs: number; endMs: number };

export type ArtifactJumpDetail = { artifactId: string; page: number | null; span?: TranscriptSpan | null };

export function jumpToArtifact(detail: ArtifactJumpDetail): void {
  window.dispatchEvent(new CustomEvent<ArtifactJumpDetail>(ARTIFACT_JUMP_EVENT, { detail }));
}

export function onArtifactJump(handler: (detail: ArtifactJumpDetail) => void): () => void {
  const listener = (event: Event) => handler((event as CustomEvent<ArtifactJumpDetail>).detail);
  window.addEventListener(ARTIFACT_JUMP_EVENT, listener);
  return () => window.removeEventListener(ARTIFACT_JUMP_EVENT, listener);
}
