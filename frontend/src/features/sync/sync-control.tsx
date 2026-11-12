"use client";

import { RotateCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { FootballIcon } from "@/shared/components/football-icon";
import { cn } from "@/lib/utils";

import { useSyncStatus, useSyncUsage, useTriggerSync } from "./hooks";

/** Kalan API kotası + "Şimdi güncelle". Bütçe yetmiyorsa buton pasif. */
export function SyncControl() {
  const usage = useSyncUsage();
  const status = useSyncStatus();
  const sync = useTriggerSync();

  const running = sync.isPending || status.running !== null;
  const disabled = running || !usage.can_sync;
  const ratio = usage.daily_limit ? usage.remaining / usage.daily_limit : 0;
  const reason = running
    ? "Şu anda bir güncelleme çalışıyor"
    : !usage.can_sync
      ? `Günlük kota yetersiz: ${usage.next_sync_cost} istek gerekiyor, ${usage.remaining} kaldı`
      : `Bu güncelleme ${usage.next_sync_cost} API isteği kullanır`;

  return (
    <div className="flex items-center gap-3 rounded-2xl border bg-pitch-900/60 p-2 pl-4">
      <div className="w-32" aria-label={`API kotası: ${usage.remaining} / ${usage.daily_limit}`}>
        <div className="flex items-baseline justify-between text-xs">
          <span className="text-sage">API kotası</span>
          <span className="tabular font-bold text-chalk">
            {usage.remaining} / {usage.daily_limit}
          </span>
        </div>
        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-white/10">
          <div
            className={cn(
              "animate-grow-x h-full rounded-full",
              ratio > 0.25 ? "bg-lime" : ratio > 0.05 ? "bg-amber" : "bg-loss",
            )}
            style={{ width: `${Math.max(ratio * 100, 2)}%` }}
          />
        </div>
      </div>
      <Tooltip>
        <TooltipTrigger asChild>
          {/* Pasif butonda da ipucu görünsün diye span ile sarılı */}
          <span tabIndex={disabled ? 0 : -1}>
            <Button
              onClick={() => sync.mutate()}
              disabled={disabled}
              className="h-11 rounded-xl px-4 font-bold hover:bg-lime-bright disabled:bg-[#2a3d31] disabled:text-moss disabled:opacity-100"
            >
              {running ? (
                <>
                  <FootballIcon className="animate-spin-ball size-[18px]" /> Güncelleniyor…
                </>
              ) : (
                <>
                  <RotateCw className="size-4" /> Şimdi güncelle
                </>
              )}
            </Button>
          </span>
        </TooltipTrigger>
        <TooltipContent>{reason}</TooltipContent>
      </Tooltip>
    </div>
  );
}

export function SyncControlSkeleton() {
  return <div className="h-[60px] w-[300px] animate-pulse rounded-2xl border bg-pitch-900/60" />;
}
