"use client";

import { queryOptions, useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";

import { endpoints } from "@/lib/api/endpoints";

export const aiStatusQuery = () =>
  queryOptions({ queryKey: ["insights", "status"], queryFn: endpoints.aiStatus, staleTime: 60_000 });

export const useAiStatus = () => useSuspenseQuery(aiStatusQuery()).data;

/** Analiz üretimi (yan etkili, maliyetli) → mutation. Backend aynı veri için önbellekten döner. */
export function useCreateInsight(leagueId: number, season?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ teamAId, teamBId }: { teamAId: number; teamBId: number }) =>
      endpoints.createInsight({ leagueId, season, teamAId, teamBId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["insights", "status"] }),
  });
}
