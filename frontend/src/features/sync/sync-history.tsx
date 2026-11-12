"use client";

import type { SyncRun } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { Panel, PanelHeader } from "@/shared/components/panel";
import { EmptyState } from "@/shared/components/states";
import { dayKey, formatDay, formatTime } from "@/shared/lib/format";

import { useSyncStatus } from "./hooks";
import { RUN_LABEL, TRIGGER_LABEL } from "./labels";

const VISIBLE = 5;

export function SyncHistory() {
  const { recent } = useSyncStatus();
  return (
    <Panel className="animate-fade-up">
      <PanelHeader title="Senkronizasyon geçmişi" />
      {recent.length === 0 ? (
        <EmptyState title="Henüz senkronizasyon yok" />
      ) : (
        <ol className="divide-y divide-white/7">
          {recent.slice(0, VISIBLE).map((run, i) => (
            <li
              key={run.id}
              className="animate-fade-up flex gap-3 py-3 first:pt-0"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <span className={cn("mt-1.5 size-2.5 shrink-0 rounded-full", RUN_LABEL[run.status].dot)} />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <p className="font-semibold">{TRIGGER_LABEL[run.trigger]}</p>
                  <time className="shrink-0 text-xs text-sage" dateTime={run.started_at}>
                    {when(run.started_at)}
                  </time>
                </div>
                <p className="mt-0.5 text-sm text-sage">{detail(run)}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Panel>
  );
}

function detail(run: SyncRun) {
  if (run.status === "skipped") return run.error_message ?? "Gerek görülmedi; istek atılmadı";
  if (run.status === "failed") return `${run.requests_made} istek · ${run.error_message ?? "hata"}`;
  if (run.status === "running") return "Devam ediyor…";
  const parts = [
    `${run.requests_made} istek`,
    `${run.inserted} yeni, ${run.updated} değişen kayıt`,
    `${run.skipped} atlandı`,
  ];
  return parts.join(" · ");
}

function when(iso: string) {
  const today = dayKey(new Date().toISOString());
  const yesterday = dayKey(new Date(Date.now() - 86_400_000).toISOString());
  const day = dayKey(iso);
  if (day === today) return formatTime(iso);
  if (day === yesterday) return `Dün ${formatTime(iso)}`;
  return `${formatDay(iso)} ${formatTime(iso)}`;
}
