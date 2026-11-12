"use client";

import { useDashboardParams } from "@/features/dashboard/hooks";
import { SyncHistory } from "@/features/sync/sync-history";
import { PanelSkeleton } from "@/shared/components/panel";
import { QueryBoundary } from "@/shared/components/query-boundary";

import { GoalsByRoundChart } from "./goals-by-round-chart";
import { useOverview } from "./hooks";
import { KpiCards } from "./kpi-cards";
import { LatestResults } from "./latest-results";

const RECENT = 4;

export function OverviewView() {
  const { leagueId, season } = useDashboardParams();
  const overview = useOverview(leagueId, season);

  return (
    <div className="space-y-5">
      <KpiCards overview={overview} />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <GoalsByRoundChart rounds={overview.summary.goals_by_round} />
        <QueryBoundary fallback={<PanelSkeleton className="h-[340px]" />}>
          <SyncHistory />
        </QueryBoundary>
      </div>
      <LatestResults fixtures={overview.recent_results.slice(0, RECENT)} />
    </div>
  );
}

export function OverviewSkeleton() {
  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <PanelSkeleton key={i} className="h-[150px]" />
        ))}
      </div>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <PanelSkeleton className="h-[340px]" />
        <PanelSkeleton className="h-[340px]" />
      </div>
      <PanelSkeleton className="h-[200px]" />
    </div>
  );
}
