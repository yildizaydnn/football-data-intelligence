import type { Fixture } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { StatusBadge } from "@/shared/components/status-badge";
import { TeamCrest } from "@/shared/components/team-crest";
import { formatTime } from "@/shared/lib/format";

export function MatchRow({ fixture, onOpen }: { fixture: Fixture; onOpen: () => void }) {
  const { home_goals: hg, away_goals: ag } = fixture;
  const scored = hg !== null && ag !== null;
  const final = fixture.status === "finished";
  const homeWon = final && scored && hg > ag;
  const awayWon = final && scored && ag > hg;

  return (
    <li>
      <button
        type="button"
        onClick={onOpen}
        aria-label={`${fixture.home_team.name} - ${fixture.away_team.name} maç detayı`}
        className="grid w-full grid-cols-[48px_1fr_auto_1fr] items-center gap-3 px-4 py-4 text-left transition-colors hover:bg-white/3 focus-visible:bg-white/5 focus-visible:outline-none sm:grid-cols-[64px_1fr_96px_1fr_110px] sm:px-5"
      >
        <time className="tabular text-sm text-sage" dateTime={fixture.kickoff_at}>
          {formatTime(fixture.kickoff_at)}
        </time>
        <span
          className={cn(
            "flex min-w-0 items-center justify-end gap-2 text-right text-sm",
            homeWon ? "font-bold text-white" : "font-medium text-mist",
          )}
        >
          <span className="truncate">{fixture.home_team.name}</span>
          <TeamCrest team={fixture.home_team} size={22} />
        </span>
        <span
          className={cn(
            "font-display tabular min-w-14 text-center text-2xl font-extrabold",
            scored ? "text-white" : "text-moss",
          )}
        >
          {scored ? `${hg} – ${ag}` : "vs"}
        </span>
        <span
          className={cn(
            "flex min-w-0 items-center gap-2 text-sm",
            awayWon ? "font-bold text-white" : "font-medium text-mist",
          )}
        >
          <TeamCrest team={fixture.away_team} size={22} />
          <span className="truncate">{fixture.away_team.name}</span>
        </span>
        <span className="col-span-4 flex justify-end sm:col-span-1">
          <StatusBadge status={fixture.status} />
        </span>
      </button>
    </li>
  );
}
