"use client";

import Link from "next/link";

import { useDashboardParams } from "@/features/dashboard/hooks";
import type { Fixture } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { Panel, PanelHeader } from "@/shared/components/panel";
import { EmptyState } from "@/shared/components/states";
import { StatusBadge } from "@/shared/components/status-badge";
import { TeamCrest } from "@/shared/components/team-crest";
import { formatDay } from "@/shared/lib/format";

export function LatestResults({ fixtures }: { fixtures: Fixture[] }) {
  const { href } = useDashboardParams();
  return (
    <Panel className="animate-fade-up">
      <PanelHeader
        title="Son sonuçlar"
        aside={
          <Link
            href={href("/matches")}
            className="rounded-full border border-white/14 px-3.5 py-1.5 text-sm font-medium text-chalk transition-colors hover:border-white/30"
          >
            Tüm maçlar →
          </Link>
        }
      />
      {fixtures.length === 0 ? (
        <EmptyState title="Henüz tamamlanan maç yok" />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {fixtures.map((fixture, i) => (
            <ResultCard key={fixture.id} fixture={fixture} delay={i * 0.06} />
          ))}
        </div>
      )}
    </Panel>
  );
}

function ResultCard({ fixture, delay }: { fixture: Fixture; delay: number }) {
  const { home_goals: hg, away_goals: ag } = fixture;
  const scored = hg !== null && ag !== null;
  return (
    <article
      className="animate-fade-up rounded-2xl border bg-pitch-900/50 p-4"
      style={{ animationDelay: `${delay}s` }}
    >
      <div className="flex items-center justify-between text-xs text-sage">
        <time dateTime={fixture.kickoff_at}>{formatDay(fixture.kickoff_at)}</time>
        <StatusBadge status={fixture.status} />
      </div>
      <div className="mt-3 space-y-2">
        <ScoreLine team={fixture.home_team} goals={hg} won={scored && hg > ag} />
        <ScoreLine team={fixture.away_team} goals={ag} won={scored && ag > hg} />
      </div>
    </article>
  );
}

function ScoreLine({
  team,
  goals,
  won,
}: {
  team: Fixture["home_team"];
  goals: number | null;
  won: boolean;
}) {
  return (
    <div className={cn("flex items-center gap-2.5", won ? "text-white" : "text-mist")}>
      <TeamCrest team={team} size={22} />
      <span className={cn("min-w-0 flex-1 truncate text-sm", won && "font-bold")}>{team.name}</span>
      <span className="font-display tabular w-6 text-right text-2xl font-extrabold leading-none">
        {goals ?? "-"}
      </span>
    </div>
  );
}
