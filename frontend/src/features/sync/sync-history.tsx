"use client";

import { Info } from "lucide-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useDashboardParams, useLeagues } from "@/features/dashboard/hooks";
import type { SyncRun } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { Panel, PanelHeader } from "@/shared/components/panel";
import { EmptyState } from "@/shared/components/states";
import { dayKey, formatDay, formatSeason, formatTime } from "@/shared/lib/format";

import { useSyncStatus } from "./hooks";
import { apiUsageText, describeRun, RUN_LABEL, TRIGGER_LABEL } from "./labels";

const VISIBLE = 5;

/** Görüntülenen ligin veri güncellemeleri, teknik olmayan bir dille. */
export function SyncHistory() {
  const { leagueId } = useDashboardParams();
  const { recent } = useSyncStatus(leagueId);
  const league = useLeagues().find((l) => l.id === leagueId);

  return (
    <Panel className="animate-fade-up">
      <PanelHeader
        title={
          <span className="inline-flex items-center gap-2">
            Veri güncellemeleri
            <Tooltip>
              <TooltipTrigger aria-label="Bu panel ne gösteriyor?" className="text-sage hover:text-chalk">
                <Info className="size-4" />
              </TooltipTrigger>
              <TooltipContent className="max-w-72 text-xs leading-relaxed">
                Maç verileri API-Football&apos;dan çekilir. Her satır bir güncelleme işlemidir.
                Ücretsiz planda günde 100 istek hakkımız var; uygulama bu hakkı gereksiz yere
                harcamamak için bitmiş sezonlarda veri sağlayıcıya hiç sormaz.
              </TooltipContent>
            </Tooltip>
          </span>
        }
        aside={league?.name}
      />
      {recent.length === 0 ? (
        <EmptyState title="Bu lig için henüz güncelleme yapılmadı" />
      ) : (
        <ol className="divide-y divide-white/7">
          {recent.slice(0, VISIBLE).map((run, i) => (
            <RunItem key={run.id} run={run} delay={i * 0.05} />
          ))}
        </ol>
      )}
    </Panel>
  );
}

function RunItem({ run, delay }: { run: SyncRun; delay: number }) {
  const status = RUN_LABEL[run.status];
  const usage = apiUsageText(run);
  return (
    <li className="animate-fade-up flex gap-3 py-3 first:pt-0" style={{ animationDelay: `${delay}s` }}>
      <span className={cn("mt-1.5 size-2.5 shrink-0 rounded-full", status.dot)} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <p className="font-semibold">{TRIGGER_LABEL[run.trigger]}</p>
          <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold", status.badge)}>
            {status.short}
          </span>
          <time className="ml-auto text-xs text-sage" dateTime={run.started_at}>
            {when(run.started_at)}
          </time>
        </div>
        {run.season && <p className="text-xs text-mist">{formatSeason(run.season)} sezonu</p>}
        <p
          className="mt-1 text-sm text-sage"
          // Teknik ayrıntı (ör. HTTP 429) isteyen için fareyle üzerine gelince
          title={run.status === "failed" ? (run.error_message ?? undefined) : undefined}
        >
          {describeRun(run)}
        </p>
        {usage && <p className="mt-0.5 text-xs text-moss">{usage}</p>}
      </div>
    </li>
  );
}

function when(iso: string) {
  const today = dayKey(new Date().toISOString());
  const yesterday = dayKey(new Date(Date.now() - 86_400_000).toISOString());
  const day = dayKey(iso);
  if (day === today) return `Bugün ${formatTime(iso)}`;
  if (day === yesterday) return `Dün ${formatTime(iso)}`;
  return `${formatDay(iso)} ${formatTime(iso)}`;
}
