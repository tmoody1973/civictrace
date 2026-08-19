"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export const caseKeys = {
  all: ["cases"] as const,
  summary: (caseId: string) => ["cases", caseId, "summary"] as const,
  trace: (caseId: string) => ["cases", caseId, "trace"] as const,
};

export function useCaseList() {
  return useQuery({ queryKey: caseKeys.all, queryFn: api.listCases });
}

export function useCaseSummary(caseId: string) {
  return useQuery({ queryKey: caseKeys.summary(caseId), queryFn: () => api.caseSummary(caseId) });
}

export function useCaseTrace(caseId: string) {
  return useQuery({ queryKey: caseKeys.trace(caseId), queryFn: () => api.caseTrace(caseId) });
}
