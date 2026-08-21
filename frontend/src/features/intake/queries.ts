"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { CandidateBundleView, IntakeSelectionPayload } from "@/lib/api-types";

const POLL_MS = 5_000;

export const intakeKeys = {
  bundle: (bundleId: string) => ["intake", "bundles", bundleId] as const,
};

export function useIntakeLookup() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (fileNumber: string) => api.intakeLookup(fileNumber),
    onSuccess: (bundle: CandidateBundleView) => {
      client.setQueryData(intakeKeys.bundle(bundle.bundle_id), bundle);
    },
  });
}

/** Polls while the worker is creating the case, so the journalist watches it happen. */
export function useIntakeBundle(bundleId: string | null) {
  return useQuery({
    queryKey: intakeKeys.bundle(bundleId ?? "none"),
    queryFn: () => api.intakeBundle(bundleId as string),
    enabled: bundleId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "APPROVED" || status === "CREATING" ? POLL_MS : false;
    },
  });
}

export function useIntakeApprove(bundleId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (selection: IntakeSelectionPayload) => api.intakeApprove(bundleId, selection),
    onSuccess: (bundle: CandidateBundleView) => {
      client.setQueryData(intakeKeys.bundle(bundle.bundle_id), bundle);
    },
  });
}
