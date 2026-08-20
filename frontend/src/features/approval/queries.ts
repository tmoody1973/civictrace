"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api";
import { caseKeys } from "@/features/case/queries";

export const approvalKeys = {
  inquiry: (caseId: string) => ["cases", caseId, "inquiry"] as const,
  packet: (caseId: string) => ["cases", caseId, "packet"] as const,
};

/** 404 means "nothing staged / no packet yet" — a state, not an error. */
function nullOn404<T>(promise: Promise<T>): Promise<T | null> {
  return promise.catch((error: unknown) => {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  });
}

export function useStagedInquiry(caseId: string) {
  return useQuery({
    queryKey: approvalKeys.inquiry(caseId),
    queryFn: () => nullOn404(api.stagedInquiry(caseId)),
  });
}

export function usePacket(caseId: string) {
  return useQuery({
    queryKey: approvalKeys.packet(caseId),
    queryFn: () => nullOn404(api.casePacket(caseId)),
  });
}

function useRefreshCase(caseId: string) {
  const client = useQueryClient();
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: approvalKeys.packet(caseId) }),
      client.invalidateQueries({ queryKey: caseKeys.trace(caseId) }),
    ]);
}

export function useApproveInquiry(caseId: string) {
  const refresh = useRefreshCase(caseId);
  return useMutation({
    mutationFn: (body: { reviewer_name: string; artifact_hash: string }) =>
      api.approveInquiry(caseId, body),
    onSettled: refresh,
  });
}

export function useRejectInquiry(caseId: string) {
  const refresh = useRefreshCase(caseId);
  return useMutation({
    mutationFn: (body: { reviewer_name: string; note: string }) => api.rejectInquiry(caseId, body),
    onSettled: refresh,
  });
}
