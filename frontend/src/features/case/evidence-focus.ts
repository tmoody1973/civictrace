// Tiny bridge between the Decision Delta chips and the Evidence Trace rows (MOO-698 listens).
// A DOM event keeps the two features decoupled: no shared store, no prop drilling across panes.

export const EVIDENCE_FOCUS_EVENT = "civictrace:focus-evidence";

export type EvidenceFocusDetail = { evidenceId: string };

export function focusEvidence(evidenceId: string): void {
  window.dispatchEvent(new CustomEvent<EvidenceFocusDetail>(EVIDENCE_FOCUS_EVENT, { detail: { evidenceId } }));
}

export function onEvidenceFocus(handler: (detail: EvidenceFocusDetail) => void): () => void {
  const listener = (event: Event) => handler((event as CustomEvent<EvidenceFocusDetail>).detail);
  window.addEventListener(EVIDENCE_FOCUS_EVENT, listener);
  return () => window.removeEventListener(EVIDENCE_FOCUS_EVENT, listener);
}
