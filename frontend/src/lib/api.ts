// The only place the frontend talks to the backend. Visual components import hooks from
// features/, never this file's fetch. No AI/provider keys live in the browser.

import type {
  ApiEnvelope,
  ApprovalResultView,
  CandidateBundleView,
  CaseSummaryView,
  HealthResponse,
  InquiryStagedView,
  IntakeSelectionPayload,
  MatterSearchResultView,
  PacketView,
  TraceResponse,
  TranscriptView,
} from "@/lib/api-types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Shared dev bearer for the cloud API, read from frontend/.env.local (gitignored).
// Empty in plain local mode, so local dev sends no auth header at all.
const API_BEARER = process.env.NEXT_PUBLIC_API_BEARER ?? "";

export function authHeaders(): Record<string, string> {
  return API_BEARER ? { Authorization: `Bearer ${API_BEARER}` } : {};
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = "ApiError";
  }
}

function isEnvelope(value: unknown): value is ApiEnvelope<unknown> {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.ok === "boolean" && "data" in candidate && "error" in candidate;
}

/** Turn a raw envelope into data, or throw an ApiError with the backend's own words. */
export function unwrapEnvelope<T>(body: unknown, status: number): T {
  if (!isEnvelope(body)) {
    throw new ApiError(`Unexpected response shape from the API (HTTP ${status})`, status);
  }
  if (!body.ok) throw new ApiError(body.error ?? `Request failed (HTTP ${status})`, status);
  return body.data as T;
}

async function getJson<T>(path: string, fetchImpl: typeof fetch = fetch): Promise<T> {
  let response: Response;
  try {
    response = await fetchImpl(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json", ...authHeaders() },
    });
  } catch (cause) {
    throw new ApiError(`Cannot reach the CivicTrace API at ${API_BASE_URL}`, null, { cause });
  }
  const body: unknown = await response.json().catch(() => null);
  return unwrapEnvelope<T>(body, response.status);
}

async function postJson<T>(path: string, payload: unknown, fetchImpl: typeof fetch = fetch): Promise<T> {
  let response: Response;
  try {
    response = await fetchImpl(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
  } catch (cause) {
    throw new ApiError(`Cannot reach the CivicTrace API at ${API_BASE_URL}`, null, { cause });
  }
  const body: unknown = await response.json().catch(() => null);
  return unwrapEnvelope<T>(body, response.status);
}

export const api = {
  // /health, not /healthz: Google's front end swallows the exact path /healthz on run.app.
  health: () => getJson<HealthResponse>("/health"),
  listCases: () => getJson<CaseSummaryView[]>("/cases"),
  caseSummary: (caseId: string) => getJson<CaseSummaryView>(`/cases/${encodeURIComponent(caseId)}`),
  caseTrace: (caseId: string) => getJson<TraceResponse>(`/cases/${encodeURIComponent(caseId)}/trace`),
  artifactFileUrl: (artifactId: string) => `${API_BASE_URL}/artifacts/${encodeURIComponent(artifactId)}/file`,
  artifactTranscript: (artifactId: string) =>
    getJson<TranscriptView>(`/artifacts/${encodeURIComponent(artifactId)}/transcript`),
  stagedInquiry: (caseId: string) => getJson<InquiryStagedView>(`/cases/${encodeURIComponent(caseId)}/inquiry`),
  casePacket: (caseId: string) => getJson<PacketView>(`/cases/${encodeURIComponent(caseId)}/packet`),
  approveInquiry: (caseId: string, body: { reviewer_name: string; artifact_hash: string }) =>
    postJson<ApprovalResultView>(`/cases/${encodeURIComponent(caseId)}/inquiry/approve`, body),
  rejectInquiry: (caseId: string, body: { reviewer_name: string; note: string }) =>
    postJson<null>(`/cases/${encodeURIComponent(caseId)}/inquiry/reject`, body),
  intakeSearch: (query: string) =>
    postJson<MatterSearchResultView[]>("/intake/search", { query }),
  intakeLookup: (fileNumber: string) =>
    postJson<CandidateBundleView>("/intake/lookup", { file_number: fileNumber }),
  intakeBundle: (bundleId: string) =>
    getJson<CandidateBundleView>(`/intake/bundles/${encodeURIComponent(bundleId)}`),
  intakeApprove: (bundleId: string, selection: IntakeSelectionPayload) =>
    postJson<CandidateBundleView>(
      `/intake/bundles/${encodeURIComponent(bundleId)}/approve`,
      selection,
    ),
};
