"use client";

import {
  queryOptions,
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiError } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

/** Kalan kota + seçili lig/sezon için bir sonraki güncellemenin istek maliyeti. */
export const syncUsageQuery = (leagueId: number, season?: number) =>
  queryOptions({
    queryKey: ["sync", "usage", leagueId, season ?? "default"],
    queryFn: () => endpoints.syncUsage({ leagueId, season }),
    staleTime: 15_000,
  });

/** Çalışan sync + son işlemler. `leagueId` verilirse geçmiş o lige göre süzülür. */
export const syncStatusQuery = (leagueId?: number) =>
  queryOptions({
    queryKey: ["sync", "status", leagueId ?? "all"],
    queryFn: () => endpoints.syncStatus(leagueId),
    staleTime: 15_000,
  });

export const useSyncUsage = (leagueId: number, season?: number) =>
  useSuspenseQuery(syncUsageQuery(leagueId, season)).data;
export const useSyncStatus = (leagueId?: number) =>
  useSuspenseQuery(syncStatusQuery(leagueId)).data;

/** Elle güncelleme: ekranda görüntülenen lig ve sezon için. Bitince tüm ekranlar tazelenir. */
export function useTriggerSync(leagueId: number, season?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => endpoints.triggerSync({ leagueId, season }),
    onSuccess: (run) => {
      if (run.status === "failed") {
        toast.error("Güncelleme başarısız", { description: run.error_message ?? undefined });
      } else {
        const changes = run.inserted + run.updated;
        toast.success(run.status === "partial" ? "Güncellendi (bazı kayıtlar atlandı)" : "Güncellendi", {
          description: changes
            ? `${run.inserted} yeni, ${run.updated} değişen kayıt · ${run.requests_made} istek`
            : `Yeni veri yok · ${run.requests_made} istek`,
        });
      }
    },
    onError: (error) => {
      toast.error("Güncelleme başlatılamadı", {
        description: error instanceof ApiError ? error.message : undefined,
      });
    },
    onSettled: () => queryClient.invalidateQueries(),
  });
}
