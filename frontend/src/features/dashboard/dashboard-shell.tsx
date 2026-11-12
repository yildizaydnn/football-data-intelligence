"use client";

import Link from "next/link";
import { notFound, usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { SyncAlert } from "@/features/sync/sync-alert";
import { SyncControl, SyncControlSkeleton } from "@/features/sync/sync-control";
import { FootballIcon } from "@/shared/components/football-icon";
import { QueryBoundary } from "@/shared/components/query-boundary";

import { Hero, Pitch } from "./hero";
import { useDashboardParams, useLeagues } from "./hooks";
import { LeagueSeasonSelect } from "./league-season-select";
import { NavTabs } from "./nav-tabs";

/** Tüm lig sayfalarının ortak çerçevesi: üst bar, hero, sekmeler. */
export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { leagueId } = useDashboardParams();
  const leagues = useLeagues();
  if (!leagues.some((league) => league.id === leagueId)) notFound();
  const isOverview = pathname === `/leagues/${leagueId}`;

  return (
    <div className="min-h-dvh">
      <TopBar
        select={
          <QueryBoundary fallback={<SelectSkeleton />} inline>
            <LeagueSeasonSelect />
          </QueryBoundary>
        }
        sync={
          <QueryBoundary fallback={<SyncControlSkeleton />} inline>
            <SyncControl />
          </QueryBoundary>
        }
      />
      <QueryBoundary fallback={<Pitch compact={!isOverview} />} inline>
        <Hero compact={!isOverview} />
      </QueryBoundary>
      <div className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-12">
        <NavTabs />
        <QueryBoundary fallback={null} inline>
          <SyncAlert />
        </QueryBoundary>
        <main className="mt-6">{children}</main>
      </div>
    </div>
  );
}

export function TopBar({ select, sync }: { select?: ReactNode; sync?: ReactNode }) {
  return (
    <header className="border-b bg-pitch-950">
      <div className="mx-auto flex max-w-7xl flex-wrap items-end justify-between gap-4 px-4 py-3 sm:px-6 lg:px-12">
        <Link href="/" className="flex items-center gap-3 self-center">
          <FootballIcon className="size-7" />
          <span className="leading-tight">
            <span className="font-display block text-xl font-extrabold uppercase">
              Football Intelligence
            </span>
            <span className="block text-xs text-sage">Veri platformu · API-Football</span>
          </span>
        </Link>
        <div className="flex flex-wrap items-end gap-3">
          {select}
          {sync}
        </div>
      </div>
    </header>
  );
}

function SelectSkeleton() {
  return (
    <div className="flex gap-2.5">
      <div className="h-[66px] w-52 animate-pulse rounded-xl bg-pitch-800/60" />
      <div className="h-[66px] w-28 animate-pulse rounded-xl bg-pitch-800/60" />
    </div>
  );
}

/** URL çözülene kadar (Suspense) gösterilen çerçeve iskeleti. */
export function DashboardShellSkeleton() {
  return (
    <div className="min-h-dvh">
      <TopBar select={<SelectSkeleton />} sync={<SyncControlSkeleton />} />
      <Pitch />
    </div>
  );
}
