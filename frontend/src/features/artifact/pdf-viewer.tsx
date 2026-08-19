"use client";

import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";
import { useMemo, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";

import { Button } from "@/components/ui/button";

// Worker ships with pdfjs-dist (pinned to react-pdf's version); bundled as an asset, no CDN.
pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

const ZOOMS = [0.75, 1, 1.25, 1.5, 2] as const;

export type PdfViewerProps = {
  bytes: ArrayBuffer;
  /** The page an anchor asked for; null when the user just opened the document. */
  anchoredPage: number | null;
  label: string;
};

/** One page at a time (some public records run 160+ pages). The anchored page gets a ring + badge. */
export function PdfViewer({ bytes, anchoredPage, label }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [page, setPage] = useState(anchoredPage ?? 1);
  const [zoomIndex, setZoomIndex] = useState(1);
  // pdf.js transfers the buffer to its worker (detaching it); hand it a private copy each load.
  const file = useMemo(() => ({ data: new Uint8Array(bytes.slice(0)) }), [bytes]);

  // A new anchor jump re-targets the page (React "adjust state while rendering" pattern, no effect).
  const [lastAnchor, setLastAnchor] = useState(anchoredPage);
  if (anchoredPage !== lastAnchor) {
    setLastAnchor(anchoredPage);
    if (anchoredPage !== null) setPage(anchoredPage);
  }

  const clamp = (next: number) => Math.min(Math.max(1, next), numPages ?? next);
  const onAnchoredPage = anchoredPage !== null && page === anchoredPage;

  return (
    <div className="flex h-full min-h-0 flex-col gap-2" data-testid="pdf-viewer">
      <div className="flex flex-wrap items-center gap-2" role="toolbar" aria-label="Page controls">
        <Button variant="outline" size="sm" onClick={() => setPage((p) => clamp(p - 1))} disabled={page <= 1} aria-label="Previous page">
          <ChevronLeft aria-hidden="true" />
        </Button>
        <span className="text-sm tabular-nums" data-testid="page-label">
          Page {page} of {numPages ?? "…"}
        </span>
        <Button variant="outline" size="sm" onClick={() => setPage((p) => clamp(p + 1))} disabled={numPages !== null && page >= numPages} aria-label="Next page">
          <ChevronRight aria-hidden="true" />
        </Button>
        <Button variant="outline" size="sm" onClick={() => setZoomIndex((z) => Math.max(0, z - 1))} disabled={zoomIndex === 0} aria-label="Zoom out">
          <ZoomOut aria-hidden="true" />
        </Button>
        <span className="text-xs tabular-nums text-muted-foreground">{Math.round(ZOOMS[zoomIndex] * 100)}%</span>
        <Button variant="outline" size="sm" onClick={() => setZoomIndex((z) => Math.min(ZOOMS.length - 1, z + 1))} disabled={zoomIndex === ZOOMS.length - 1} aria-label="Zoom in">
          <ZoomIn aria-hidden="true" />
        </Button>
        {anchoredPage !== null ? (
          <Button variant={onAnchoredPage ? "default" : "secondary"} size="sm" onClick={() => setPage(anchoredPage)} data-testid="anchored-page-badge">
            Anchored page {anchoredPage}
          </Button>
        ) : null}
      </div>
      <p className="sr-only" aria-live="polite" data-testid="page-announcement">
        {label}: showing page {page} of {numPages ?? "unknown"}
        {onAnchoredPage ? " — this is the anchored page" : ""}
      </p>
      <div className="min-h-0 flex-1 overflow-auto">
        <Document
          file={file}
          onLoadSuccess={(pdf) => setNumPages(pdf.numPages)}
          loading={<p className="text-sm text-muted-foreground">Rendering document…</p>}
          error={<p className="text-sm text-destructive">This file could not be rendered as a PDF.</p>}
        >
          <div className={onAnchoredPage ? "inline-block rounded ring-4 ring-ring ring-offset-2" : "inline-block"} data-testid="page-frame">
            <Page pageNumber={page} scale={ZOOMS[zoomIndex]} renderAnnotationLayer={false} renderTextLayer />
          </div>
        </Document>
      </div>
    </div>
  );
}
