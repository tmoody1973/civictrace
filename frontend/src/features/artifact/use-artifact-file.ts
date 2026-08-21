"use client";

import { useQuery } from "@tanstack/react-query";

import { sha256Hex } from "@/features/artifact/hash";
import { api, ApiError, authHeaders, unwrapEnvelope } from "@/lib/api";

export type ArtifactFile = {
  artifactId: string;
  bytes: ArrayBuffer;
  mimeType: string;
  headerHash: string | null;
  computedHash: string;
};

/** Bytes come only from our backend; we keep the hash header and hash the bytes ourselves. */
export async function fetchArtifactFile(artifactId: string, fetchImpl: typeof fetch = fetch): Promise<ArtifactFile> {
  let response: Response;
  try {
    response = await fetchImpl(api.artifactFileUrl(artifactId), { headers: authHeaders() });
  } catch (cause) {
    throw new ApiError("Cannot reach the CivicTrace API for this document", null, { cause });
  }
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    unwrapEnvelope(body, response.status); // throws ApiError with the backend's words
    throw new ApiError(`Document request failed (HTTP ${response.status})`, response.status);
  }
  const bytes = await response.arrayBuffer();
  return {
    artifactId,
    bytes,
    mimeType: (response.headers.get("content-type") ?? "application/octet-stream").split(";")[0].trim(),
    headerHash: response.headers.get("x-civictrace-content-hash"),
    computedHash: await sha256Hex(bytes),
  };
}

export function useArtifactFile(artifactId: string | null) {
  return useQuery({
    queryKey: ["artifacts", artifactId, "file"],
    queryFn: () => fetchArtifactFile(artifactId as string),
    enabled: artifactId !== null,
    staleTime: Infinity,
  });
}
