// Every user-facing sentence for the approval drawer and packet view. Joins the same
// vocabulary test as the case copy: no allegation words, record-grounded phrasing only.

export const APPROVAL_COPY = {
  drawerTitle: "Human approval",
  drawerDetail:
    "Approval is a deliberate final action. You approve the exact bytes shown here — nothing else.",
  question: "Proposed next question",
  scope: "Why this scope",
  target: "Target record or source",
  excluded: "Expressly excluded",
  citedEvidence: "Cited evidence",
  limitations: "Limitations",
  hashLabel: "Fingerprint (SHA-256) of this exact proposal",
  hashDetail: "The approval binds to this fingerprint. If the proposal changes, the approval dies with it.",
  ttl: (minutes: number) => `An approval expires ${minutes} minutes after it is issued.`,
  reviewerLabel: "Your name (reviewer of record)",
  reviewerHonesty: "Identity is a typed name for now; sign-in arrives with the cloud deploy.",
  approveButton: "Approve and render the DRAFT packet",
  rejectButton: "Reject with a note",
  noteLabel: "Why you are rejecting (recorded in the ledger)",
  approving: "Checking the fingerprint and rendering…",
  approvedTitle: "Approved — DRAFT packet rendered",
  approvedDetail: "The token and the packet fingerprint are recorded in the ledger.",
  tokenLabel: "Approval token",
  expiresLabel: "Token expires",
  rejectedTitle: "Rejected — recorded in the ledger",
  rejectedDetail: "No packet was rendered. The note is part of the case record.",
  refusedTitle: "Approval refused — nothing was rendered",
  refusedDetail: "The system fails closed. The refusal reason is recorded in the ledger.",
  noInquiryTitle: "No staged question yet",
  noInquiryDetail: "A question appears here after a Decision Delta is staged and its checks pass.",
  needName: "Type your name to approve or reject.",
  needNote: "A rejection needs a note.",
  packetTitle: "DRAFT inquiry packet",
  packetBanner: "DRAFT ONLY — not sent; no external action taken.",
  packetHashLabel: "Fingerprint (SHA-256) of the rendered packet",
  noPacketTitle: "No packet rendered",
  noPacketDetail: "The packet appears here after a human approves the staged question.",
} as const;

/** Every string above, flattened, for the vocabulary test. */
export function allApprovalCopy(): string[] {
  const texts: string[] = [];
  for (const value of Object.values(APPROVAL_COPY)) {
    texts.push(typeof value === "string" ? value : value(30));
  }
  return texts;
}
