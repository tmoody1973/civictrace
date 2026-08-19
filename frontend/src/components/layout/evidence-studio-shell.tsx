"use client";

import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";

/**
 * Desktop-first three-pane studio (frontend/README.md "First Screen"):
 *   case & evidence rail | original source | Decision Delta & human review
 *   ───────────────── evidence timeline beneath all panes ─────────────────
 * Pure layout. Panes receive finished content; they fetch nothing.
 */
export function EvidenceStudioShell({
  rail,
  source,
  review,
  timeline,
}: {
  rail: React.ReactNode;
  source: React.ReactNode;
  review: React.ReactNode;
  timeline: React.ReactNode;
}) {
  return (
    <ResizablePanelGroup orientation="vertical" className="h-full min-h-0 flex-1">
      <ResizablePanel defaultSize="72" minSize="40">
        <ResizablePanelGroup orientation="horizontal" className="h-full">
          <ResizablePanel defaultSize="22" minSize={220}>
            <Pane label="Case and evidence">{rail}</Pane>
          </ResizablePanel>
          <ResizableHandle withHandle aria-label="Resize case rail" />
          <ResizablePanel defaultSize="48" minSize={320}>
            <Pane label="Original source">{source}</Pane>
          </ResizablePanel>
          <ResizableHandle withHandle aria-label="Resize source viewer" />
          <ResizablePanel defaultSize="30" minSize={280}>
            <Pane label="Decision Delta and human review">{review}</Pane>
          </ResizablePanel>
        </ResizablePanelGroup>
      </ResizablePanel>
      <ResizableHandle withHandle aria-label="Resize evidence timeline" />
      <ResizablePanel defaultSize="28" minSize={120}>
        <Pane label="Evidence timeline">{timeline}</Pane>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}

function Pane({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <section aria-label={label} className="flex h-full min-h-0 flex-col overflow-auto p-4">
      <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</h2>
      <div className="min-h-0 flex-1">{children}</div>
    </section>
  );
}
