import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("react-pdf", () => ({
  pdfjs: { GlobalWorkerOptions: { workerSrc: "" } },
  Document: ({ children, onLoadSuccess }: { children: React.ReactNode; onLoadSuccess?: (pdf: { numPages: number }) => void }) => {
    onLoadSuccess?.({ numPages: 12 });
    return <div data-testid="mock-document">{children}</div>;
  },
  Page: ({ pageNumber }: { pageNumber: number }) => <div data-testid="mock-page">page {pageNumber}</div>,
}));
vi.mock("react-pdf/dist/Page/TextLayer.css", () => ({}));

import { ArtifactHeader } from "@/features/artifact/artifact-header";
import { PdfViewer } from "@/features/artifact/pdf-viewer";
import { fetchArtifactFile } from "@/features/artifact/use-artifact-file";
import { ApiError } from "@/lib/api";

const bytes = new TextEncoder().encode("%PDF-fake").buffer as ArrayBuffer;

describe("PdfViewer", () => {
  it("opens on the anchored page, labels it, and re-jumps when the anchor changes", () => {
    const { rerender } = render(<PdfViewer bytes={bytes} anchoredPage={3} label="tid121-amendment-1-2026" />);
    expect(screen.getByTestId("page-label")).toHaveTextContent("Page 3 of 12");
    expect(screen.getByTestId("mock-page")).toHaveTextContent("page 3");
    expect(screen.getByTestId("anchored-page-badge")).toHaveTextContent("Anchored page 3");
    expect(screen.getByTestId("page-frame").className).toMatch(/ring-4/);
    expect(screen.getByTestId("page-announcement")).toHaveTextContent("this is the anchored page");

    fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    expect(screen.getByTestId("page-label")).toHaveTextContent("Page 4 of 12");
    expect(screen.getByTestId("page-frame").className).not.toMatch(/ring-4/);

    rerender(<PdfViewer bytes={bytes} anchoredPage={5} label="tid121-project-plan-2024" />);
    expect(screen.getByTestId("page-label")).toHaveTextContent("Page 5 of 12");
  });

  it("clamps navigation to the document", () => {
    render(<PdfViewer bytes={bytes} anchoredPage={null} label="x" />);
    expect(screen.getByRole("button", { name: "Previous page" })).toBeDisabled();
    for (let i = 0; i < 20; i++) fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    expect(screen.getByTestId("page-label")).toHaveTextContent("Page 12 of 12");
    expect(screen.getByRole("button", { name: "Next page" })).toBeDisabled();
  });
});

describe("ArtifactHeader hash verdict", () => {
  const info = { artifactId: "a", canonicalUrl: "https://milwaukee.legistar1.com/x.pdf", retrievedAt: "2026-08-19T18:07:47Z", ledgerHash: "sha256:aaa" };
  it("says Matches ledger when bytes hash equals the ledger hash", () => {
    render(<ArtifactHeader info={info} headerHash="sha256:aaa" computedHash="sha256:aaa" />);
    expect(screen.getByTestId("hash-verdict")).toHaveTextContent("Matches ledger");
  });
  it("says Does not match when the bytes differ", () => {
    render(<ArtifactHeader info={info} headerHash="sha256:aaa" computedHash="sha256:bbb" />);
    expect(screen.getByTestId("hash-verdict")).toHaveTextContent("Does not match");
  });
  it("says Not checked while loading", () => {
    render(<ArtifactHeader info={info} headerHash={null} computedHash={null} />);
    expect(screen.getByTestId("hash-verdict")).toHaveTextContent("Not checked");
  });
});

describe("fetchArtifactFile", () => {
  it("returns bytes, mime, header hash and a computed hash", async () => {
    const fetchImpl = vi.fn(async () =>
      new Response(new TextEncoder().encode("abc"), {
        status: 200,
        headers: { "content-type": "application/pdf", "x-civictrace-content-hash": "sha256:h" },
      }),
    ) as unknown as typeof fetch;
    const file = await fetchArtifactFile("a", fetchImpl);
    expect(file.mimeType).toBe("application/pdf");
    expect(file.headerHash).toBe("sha256:h");
    expect(file.computedHash).toBe("sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
  });
  it("turns a 404 envelope into the backend's own words", async () => {
    const fetchImpl = vi.fn(async () =>
      new Response(JSON.stringify({ ok: false, data: null, error: "artifact 'nope' not found" }), { status: 404, headers: { "content-type": "application/json" } }),
    ) as unknown as typeof fetch;
    await expect(fetchArtifactFile("nope", fetchImpl)).rejects.toEqual(new ApiError("artifact 'nope' not found", 404));
  });
});

