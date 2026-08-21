"use client";

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function useArtifactTranscript(artifactId: string | null) {
  return useQuery({
    queryKey: ["artifacts", artifactId, "transcript"],
    queryFn: () => api.artifactTranscript(artifactId as string),
    enabled: artifactId !== null,
    staleTime: Infinity,
  });
}
