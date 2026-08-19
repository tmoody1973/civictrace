// The only place the frontend talks to the backend. Visual components import hooks from
// features/, never this file's fetch. No AI/provider keys live in the browser.

import type { ApiEnvelope, CaseSummaryView, HealthResponse, TraceResponse } from "@/lib/api-types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
    response = await fetchImpl(`${API_BASE_URL}${path}`, { headers: { Accept: "application/json" } });
  } catch (cause) {
    throw new ApiError(`Cannot reach the CivicTrace API at ${API_BASE_URL}`, null, { cause });
  }
  const body: unknown = await response.json().catch(() => null);
  return unwrapEnvelope<T>(body, response.status);
}

export const api = {
  health: () => getJson<HealthResponse>("/healthz"),
  listCases: () => getJson<CaseSummaryView[]>("/cases"),
  caseSummary: (caseId: string) => getJson<CaseSummaryView>(`/cases/${encodeURIComponent(caseId)}`),
  caseTrace: (caseId: string) => getJson<TraceResponse>(`/cases/${encodeURIComponent(caseId)}/trace`),
  artifactFileUrl: (artifactId: string) => `${API_BASE_URL}/artifacts/${encodeURIComponent(artifactId)}/file`,
};
