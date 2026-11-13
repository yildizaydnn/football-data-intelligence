"use client";

import { useDashboardParams, useLeagues } from "@/features/dashboard/hooks";
import { PanelSkeleton } from "@/shared/components/panel";
import { QueryBoundary } from "@/shared/components/query-boundary";
import { EmptyState } from "@/shared/components/states";
import { TeamCrest } from "@/shared/components/team-crest";
import { formatSeason } from "@/shared/lib/format";
import { nameLang } from "@/shared/lib/locale";

import { AiInsightPanel } from "./ai-insight-panel";
import { GoalsChart } from "./goals-chart";
import { HomeAway } from "./home-away";
import { useTeamStats } from "./hooks";
import { PointsChart } from "./points-chart";
import { SummaryCards } from "./summary-cards";
import { TeamPicker } from "./team-picker";

export function TeamAnalysisView() {
  const { teamId } = useDashboardParams();
  // Takım sayfasından ayrılırken (ör. /teams'e) bileşen bir kez daha render olabilir;
  // URL'de takım yoksa istek atılmaz.
  if (teamId === undefined) return null;
  return <TeamAnalysis teamId={teamId} />;
}

function TeamAnalysis({ teamId }: { teamId: number }) {
  const { leagueId, season } = useDashboardParams();
  const stats = useTeamStats(leagueId, teamId, season);
  const country = useLeagues().find((l) => l.id === leagueId)?.country;

  if (stats === null) {
    return (
      <div className="space-y-5">
        <div className="flex justify-end">
          <QueryBoundary fallback={<PanelSkeleton className="h-[66px] w-60" />} inline>
            <TeamPicker teamId={teamId} />
          </QueryBoundary>
        </div>
        <EmptyState
          title="Bu takım seçilen sezonda bu ligde yer almıyor"
          hint="Takım seçiciden bu sezonun takımlarından birini seçin."
        />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="animate-fade-up flex items-center gap-4">
          <TeamCrest team={stats.team} size={56} />
          <div>
            <p className="text-sm text-sage">
              Takım analizi · {formatSeason(stats.season)} · {stats.overall.played} maç
            </p>
            <h1 lang={nameLang(country)} className="font-display text-5xl font-extrabold uppercase leading-none">
              {stats.team.name}
            </h1>
          </div>
        </div>
        <QueryBoundary fallback={<PanelSkeleton className="h-[66px] w-60" />} inline>
          <TeamPicker teamId={stats.team.id} />
        </QueryBoundary>
      </header>

      {stats.overall.played === 0 ? (
        <EmptyState
          title="Bu sezonda tamamlanmış maçı yok"
          hint="Takım bu sezon ligde olmayabilir; takım seçiciden başka bir takım seçin."
        />
      ) : (
        <>
          <SummaryCards stats={stats} />
          <div className="grid gap-5 lg:grid-cols-2">
            <GoalsChart stats={stats} />
            <PointsChart stats={stats} />
          </div>
          <HomeAway stats={stats} />
          <QueryBoundary fallback={<PanelSkeleton className="h-[180px]" />} inline>
            <AiInsightPanel teamId={stats.team.id} />
          </QueryBoundary>
        </>
      )}
    </div>
  );
}

export function TeamAnalysisSkeleton() {
  return (
    <div className="space-y-5">
      <PanelSkeleton className="h-[70px] w-80" />
      <div className="grid gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }, (_, i) => (
          <PanelSkeleton key={i} className="h-[170px]" />
        ))}
      </div>
      <div className="grid gap-5 lg:grid-cols-2">
        <PanelSkeleton className="h-[330px]" />
        <PanelSkeleton className="h-[330px]" />
      </div>
    </div>
  );
}
