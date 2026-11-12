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

export const syncUsageQuery = () =>
  queryOptions({ queryKey: ["sync", "usage"], queryFn: endpoints.syncUsage, staleTime: 15_000 });

export const syncStatusQuery = () =>
  queryOptions({ queryKey: ["sync", "status"], queryFn: endpoints.syncStatus, staleTime: 15_000 });

export const useSyncUsage = () => useSuspenseQuery(syncUsageQuery()).data;
export const useSyncStatus = () => useSuspenseQuery(syncStatusQuery()).data;

/** Elle güncelleme. Bitince tüm ekranların verisi tazelenir. */
export function useTriggerSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => endpoints.triggerSync(false),
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
