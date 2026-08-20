import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApprovalDrawer } from "@/features/approval/approval-drawer";
import { PacketView } from "@/features/approval/packet-view";
import { ApiError } from "@/lib/api";
import type { InquiryStagedView, PacketView as PacketData } from "@/lib/api-types";

vi.mock("@/lib/api", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...original,
    api: {
      stagedInquiry: vi.fn(),
      casePacket: vi.fn(),
      approveInquiry: vi.fn(),
      rejectInquiry: vi.fn(),
    },
  };
});

const { api } = await import("@/lib/api");
const mocked = api as unknown as Record<keyof typeof api, ReturnType<typeof vi.fn>>;

const CASE_ID = "case-tid121-bronzeville-arts-tech-hub";
const HASH = "sha256:fad5de27db03f0afcb6d0341f799b56262deef5fdc813b780895478468f33701";

const staged: InquiryStagedView = {
  case_id: CASE_ID,
  artifact_hash: HASH,
  ttl_minutes: 30,
  proposal: {
    inquiry_type: "SOURCE_QUESTION",
    proposed_question: "Has the 2025 Annual Report of Tax Incremental Districts been published?",
    scope_rationale: "The latest supplied status record is the 2024 Annual TID Report.",
    target_record_or_source: "DCD Annual Report of Tax Incremental Districts, 2025 edition",
    supporting_evidence_ids: ["ev-tid121-plan-capital-costs", "ev-tid121-amend1-capital-costs"],
    excluded_requests: ["No personnel records.", "No student-level information."],
    approval_required: true,
    limitations: [],
  },
};

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ApprovalDrawer", () => {
  it("shows the staged question, the exact hash, chips, and exclusions", async () => {
    mocked.stagedInquiry.mockResolvedValue(staged);
    renderWithClient(<ApprovalDrawer caseId={CASE_ID} />);
    expect(await screen.findByTestId("staged-question")).toHaveTextContent("2025 Annual Report");
    expect(screen.getByTestId("proposal-hash")).toHaveTextContent(HASH);
    expect(screen.getByRole("button", { name: /ev-tid121-plan-capital-costs/ })).toBeInTheDocument();
    expect(screen.getByText("No student-level information.")).toBeInTheDocument();
    expect(screen.getByText(/expires 30 minutes/)).toBeInTheDocument();
  });

  it("shows a worded empty state when nothing is staged", async () => {
    mocked.stagedInquiry.mockResolvedValue(null);
    renderWithClient(<ApprovalDrawer caseId={CASE_ID} />);
    expect(await screen.findByText("No staged question yet")).toBeInTheDocument();
  });

  it("refuses to approve without a reviewer name", async () => {
    mocked.stagedInquiry.mockResolvedValue(staged);
    renderWithClient(<ApprovalDrawer caseId={CASE_ID} />);
    fireEvent.click(await screen.findByTestId("approve-button"));
    expect(screen.getByRole("alert")).toHaveTextContent("Type your name");
    expect(mocked.approveInquiry).not.toHaveBeenCalled();
  });

  it("approve echoes the displayed hash and shows the token on success", async () => {
    mocked.stagedInquiry.mockResolvedValue(staged);
    mocked.approveInquiry.mockResolvedValue({
      token_id: "tok_abc",
      reviewer_name: "Tarik Moody",
      expires_at: "2026-08-19T18:30:00Z",
      packet_hash: "sha256:beef",
      packet_path: "/tmp/packet.md",
    });
    renderWithClient(<ApprovalDrawer caseId={CASE_ID} />);
    fireEvent.change((await screen.findAllByRole("textbox"))[0], { target: { value: "Tarik Moody" } });
    fireEvent.click(screen.getByTestId("approve-button"));
    await waitFor(() =>
      expect(mocked.approveInquiry).toHaveBeenCalledWith(CASE_ID, {
        reviewer_name: "Tarik Moody",
        artifact_hash: HASH,
      }),
    );
    expect(await screen.findByTestId("approval-approved")).toHaveTextContent("tok_abc");
  });

  it("a 409 mismatch shows the backend's own words and the fail-closed detail", async () => {
    mocked.stagedInquiry.mockResolvedValue(staged);
    mocked.approveInquiry.mockRejectedValue(
      new ApiError("you approved different bytes than are staged", 409),
    );
    renderWithClient(<ApprovalDrawer caseId={CASE_ID} />);
    fireEvent.change((await screen.findAllByRole("textbox"))[0], { target: { value: "Tarik Moody" } });
    fireEvent.click(screen.getByTestId("approve-button"));
    const refused = await screen.findByTestId("approval-refused");
    expect(refused).toHaveTextContent("you approved different bytes than are staged");
    expect(refused).toHaveTextContent("fails closed");
  });

  it("reject needs a note, then records and shows the rejected state", async () => {
    mocked.stagedInquiry.mockResolvedValue(staged);
    mocked.rejectInquiry.mockResolvedValue(null);
    renderWithClient(<ApprovalDrawer caseId={CASE_ID} />);
    const inputs = await screen.findAllByRole("textbox");
    fireEvent.change(inputs[0], { target: { value: "Tarik Moody" } });
    fireEvent.click(screen.getByTestId("reject-button"));
    expect(screen.getByRole("alert")).toHaveTextContent("A rejection needs a note.");
    fireEvent.change(inputs[1], { target: { value: "Scope is too wide." } });
    fireEvent.click(screen.getByTestId("reject-button"));
    await waitFor(() =>
      expect(mocked.rejectInquiry).toHaveBeenCalledWith(CASE_ID, {
        reviewer_name: "Tarik Moody",
        note: "Scope is too wide.",
      }),
    );
    expect(await screen.findByTestId("approval-rejected")).toBeInTheDocument();
  });
});

describe("PacketView", () => {
  it("shows the DRAFT banner, the packet hash, and the markdown verbatim", async () => {
    const packet: PacketData = {
      case_id: CASE_ID,
      markdown: "# DRAFT — Inquiry Packet\n\n**DRAFT ONLY — not sent; no external action taken.**",
      packet_hash: "sha256:beef",
      packet_path: "/tmp/packet.md",
    };
    mocked.casePacket.mockResolvedValue(packet);
    renderWithClient(<PacketView caseId={CASE_ID} />);
    expect(await screen.findByTestId("draft-banner")).toHaveTextContent("DRAFT ONLY");
    expect(screen.getByTestId("packet-hash")).toHaveTextContent("sha256:beef");
    expect(screen.getByText(/# DRAFT — Inquiry Packet/)).toBeInTheDocument();
  });

  it("shows a worded empty state before any approval", async () => {
    mocked.casePacket.mockResolvedValue(null);
    renderWithClient(<PacketView caseId={CASE_ID} />);
    expect(await screen.findByText("No packet rendered")).toBeInTheDocument();
  });
});
