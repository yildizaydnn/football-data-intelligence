"use client";

import Link from "next/link";

import { useOverview } from "@/features/overview/hooks";
import { useSyncStatus } from "@/features/sync/hooks";
import type { Fixture } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { FootballIcon } from "@/shared/components/football-icon";
import { LiveDot } from "@/shared/components/status-badge";
import { formatDateTime, formatDay, formatSeason, formatTime } from "@/shared/lib/format";

import { useDashboardParams } from "./hooks";

/** Animasyonlu saha: kayan çim şeritleri, beyaz çizgiler, yuvarlanan top, sallanan çimler. */
export function Pitch({ compact, children }: { compact?: boolean; children?: React.ReactNode }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden transition-[height] duration-500",
        compact ? "h-[150px]" : "h-[320px]",
      )}
    >
      <div className="pitch-stripes" />
      <div className="pitch-light" />
      <PitchLines compact={compact} />
      {!compact && (
        <div className="ball-run" aria-hidden>
          <div className="ball-hop">
            <FootballIcon className="ball-spin" />
          </div>
          <div className="ball-shadow" />
        </div>
      )}
      <GrassBlades />
      <div className="relative mx-auto h-full max-w-7xl px-4 sm:px-6 lg:px-12">{children}</div>
    </div>
  );
}

function PitchLines({ compact }: { compact?: boolean }) {
  const chalk = "absolute border-2 border-white/55";
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0">
      <div className="absolute inset-y-0 left-1/2 w-0.5 -translate-x-1/2 bg-white/55" />
      {!compact && (
        <>
          <div className={cn(chalk, "left-1/2 top-[75px] size-[150px] -translate-x-1/2 rounded-full")} />
          <div className="absolute left-1/2 top-[146px] size-2 -translate-x-1/2 rounded-full bg-white/80" />
          <div className={cn(chalk, "-left-0.5 top-[60px] h-[180px] w-[150px] border-l-0")} />
          <div className={cn(chalk, "-left-0.5 top-[105px] h-[90px] w-[55px] border-l-0")} />
          <div className={cn(chalk, "-right-0.5 top-[60px] h-[180px] w-[150px] border-r-0")} />
          <div className={cn(chalk, "-right-0.5 top-[105px] h-[90px] w-[55px] border-r-0")} />
        </>
      )}
    </div>
  );
}

// Deterministik (SSR ile istemci aynı HTML'i üretsin): yükseklik/gecikme/süre sözde rastgele.
const BLADES = Array.from({ length: 150 }, (_, i) => {
  const r = Math.abs(Math.sin(i * 12.9898) * 43758.5453) % 1;
  const r2 = Math.abs(Math.sin(i * 78.233) * 12345.678) % 1;
  return { h: Math.round(12 + r * 26), delay: (-r2 * 3).toFixed(2), duration: (2.2 + r * 1.6).toFixed(2) };
});

function GrassBlades() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-0 -bottom-0.5 flex h-10 items-end justify-between"
    >
      {BLADES.map((b, i) => (
        <span
          key={i}
          className="blade"
          style={{ height: b.h, animationDelay: `${b.delay}s`, animationDuration: `${b.duration}s` }}
        />
      ))}
    </div>
  );
}

export function Hero({ compact }: { compact: boolean }) {
  const { leagueId, season, href } = useDashboardParams();
  const overview = useOverview(leagueId, season);
  const { schedule } = useSyncStatus();
  const round = overview.summary.current_round?.number;
  const featured = overview.live[0] ?? overview.recent_results[0];

  return (
    <Pitch compact={compact}>
      <div
        className={cn(
          "flex h-full items-start justify-between gap-6",
          compact ? "pt-6" : "pt-10 sm:pt-12",
        )}
      >
        <div className="animate-fade-up min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-chalk/90 sm:text-sm">
            {formatSeason(overview.season.year)} Sezonu
            {round ? ` · ${round}. Hafta` : ""}
          </p>
          <h1
            className={cn(
              "font-display font-extrabold uppercase leading-[0.9] text-white drop-shadow-[0_4px_12px_rgb(0_0_0/25%)]",
              compact ? "mt-1 text-5xl" : "mt-2 text-6xl sm:text-8xl",
            )}
          >
            {overview.league.name}
          </h1>
          {!compact && (
            <p className="mt-3 text-sm text-chalk/90">
              Son senkronizasyon:{" "}
              <b className="font-semibold text-white">
                {overview.last_sync ? formatDateTime(overview.last_sync.started_at) : "henüz yok"}
              </b>
              {" · "}
              {schedule.enabled && schedule.next_run_at
                ? `Otomatik güncelleme her gün ${formatTime(schedule.next_run_at)}`
                : "Otomatik güncelleme kapalı"}
            </p>
          )}
        </div>
        {featured && !compact && (
          <Link
            href={href("/matches", { team: featured.home_team.id })}
            className="animate-fade-up hidden shrink-0 items-center gap-3 rounded-2xl border border-white/10 bg-pitch-950/80 px-4 py-3 backdrop-blur transition-colors hover:border-white/25 md:flex"
          >
            <FeaturedMatch fixture={featured} />
          </Link>
        )}
      </div>
    </Pitch>
  );
}

function FeaturedMatch({ fixture }: { fixture: Fixture }) {
  const live = fixture.status === "live";
  return (
    <>
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold",
          live ? "bg-live/15 text-[#ff9b8f]" : "bg-white/8 text-mist",
        )}
      >
        {live ? (
          <>
            <LiveDot /> CANLI
          </>
        ) : (
          `SON MAÇ · ${formatDay(fixture.kickoff_at)}`
        )}
      </span>
      <span className="font-semibold">{fixture.home_team.name}</span>
      <span className="font-display tabular text-3xl font-extrabold">
        {fixture.home_goals ?? "-"} – {fixture.away_goals ?? "-"}
      </span>
      <span className="font-semibold">{fixture.away_team.name}</span>
    </>
  );
}
