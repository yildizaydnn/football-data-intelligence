"use client";

import { useRouter } from "next/navigation";
import { useRef } from "react";

import { useDashboardParams } from "@/features/dashboard/hooks";
import type { StandingRow } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { FormStrip } from "@/shared/components/form-chip";
import { Panel, PanelHeader, PanelSkeleton } from "@/shared/components/panel";
import { EmptyState } from "@/shared/components/states";
import { TeamCrest } from "@/shared/components/team-crest";
import { useFlip } from "@/shared/hooks/use-flip";
import { formatSeason, formatSigned } from "@/shared/lib/format";

import { useStandings } from "./hooks";

const TOP = 4;
const BOTTOM = 3;

export function StandingsTable() {
  const router = useRouter();
  const { leagueId, season, href } = useDashboardParams();
  const standings = useStandings(leagueId, season);
  const rows = standings.rows;
  const body = useRef<HTMLTableSectionElement>(null);
  useFlip(body, [rows]);

  if (rows.length === 0) {
    return (
      <Panel>
        <PanelHeader title="Puan tablosu" />
        <EmptyState title="Bu sezon için henüz oynanmış maç yok" />
      </Panel>
    );
  }

  const open = (row: StandingRow) => router.push(href(`/teams/${row.team.id}`));

  return (
    <Panel className="animate-fade-up overflow-hidden p-0 sm:p-0">
      <PanelHeader
        className="px-5 pt-5 sm:px-6 sm:pt-6"
        title="Puan tablosu"
        aside={`${formatSeason(standings.season)} · veritabanındaki maç sonuçlarından hesaplandı`}
      />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[340px] text-sm">
          <thead>
            <tr className="border-b text-[11px] font-semibold uppercase tracking-widest text-sage">
              <Th className="w-12 pl-5 text-left sm:pl-6">#</Th>
              <Th className="text-left">Takım</Th>
              <Th title="Oynanan maç">O</Th>
              <Th title="Galibiyet" hideBelow="sm">G</Th>
              <Th title="Beraberlik" hideBelow="sm">B</Th>
              <Th title="Mağlubiyet" hideBelow="sm">M</Th>
              <Th title="Attığı : yediği gol" hideBelow="md">Gol</Th>
              <Th title="Averaj">Av</Th>
              <Th hideBelow="lg">Son 5</Th>
              <Th className="pr-5 sm:pr-6">P</Th>
            </tr>
          </thead>
          <tbody ref={body}>
            {rows.map((row) => (
              <tr
                key={row.team.id}
                data-flip-key={row.team.id}
                tabIndex={0}
                onClick={() => open(row)}
                onKeyDown={(e) => e.key === "Enter" && open(row)}
                className="group cursor-pointer border-b border-white/7 last:border-0 hover:bg-white/3 focus-visible:bg-white/5 focus-visible:outline-none"
                aria-label={`${row.position}. ${row.team.name}, ${row.points} puan — takım analizine git`}
              >
                <td className="py-3 pl-5 sm:pl-6">
                  <RankBadge position={row.position} total={rows.length} />
                </td>
                <td className="py-3">
                  <span className="flex items-center gap-2.5 font-semibold">
                    <TeamCrest team={row.team} size={22} />
                    <span className="truncate group-hover:text-lime">{row.team.name}</span>
                  </span>
                </td>
                <Td>{row.played}</Td>
                <Td hideBelow="sm">{row.won}</Td>
                <Td hideBelow="sm">{row.drawn}</Td>
                <Td hideBelow="sm">{row.lost}</Td>
                <Td hideBelow="md">
                  {row.goals_for}:{row.goals_against}
                </Td>
                <Td
                  className={cn(
                    "font-semibold",
                    row.goal_difference > 0 ? "text-win" : row.goal_difference < 0 ? "text-[#ff8a7a]" : "text-mist",
                  )}
                >
                  {formatSigned(row.goal_difference)}
                </Td>
                <td className="hidden py-3 lg:table-cell">
                  <FormStrip form={row.form} className="justify-center" />
                </td>
                <td className="font-display tabular py-3 pr-5 text-center text-2xl font-extrabold sm:pr-6">
                  {row.points}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <footer className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t px-5 py-4 text-xs text-sage sm:px-6">
        <Legend className="bg-lime" label="Lider" />
        <Legend className="bg-pitch-500" label={`İlk ${TOP}`} />
        <Legend className="bg-loss/70" label={`Son ${BOTTOM}`} />
        <span>O: oynanan · G: galibiyet · B: beraberlik · M: mağlubiyet · Av: averaj · P: puan</span>
        <span>Puan eşitliğinde: ikili puan → ikili averaj → genel averaj → atılan gol</span>
      </footer>
    </Panel>
  );
}

function RankBadge({ position, total }: { position: number; total: number }) {
  const style =
    position === 1
      ? "bg-lime text-pitch-900"
      : position <= TOP
        ? "bg-pitch-500 text-chalk"
        : position > total - BOTTOM
          ? "bg-loss/25 text-[#ffb3a8]"
          : "bg-white/6 text-chalk";
  return (
    <span className={cn("tabular grid size-7 place-items-center rounded-lg text-[13px] font-bold", style)}>
      {position}
    </span>
  );
}

type Hide = "sm" | "md" | "lg";
const HIDE: Record<Hide, string> = {
  sm: "hidden sm:table-cell",
  md: "hidden md:table-cell",
  lg: "hidden lg:table-cell",
};

function Th({
  children,
  className,
  title,
  hideBelow,
}: {
  children: React.ReactNode;
  className?: string;
  title?: string;
  hideBelow?: Hide;
}) {
  return (
    <th scope="col" title={title} className={cn("py-3 text-center", hideBelow && HIDE[hideBelow], className)}>
      {children}
    </th>
  );
}

function Td({
  children,
  className,
  hideBelow,
}: {
  children: React.ReactNode;
  className?: string;
  hideBelow?: Hide;
}) {
  return (
    <td className={cn("tabular py-3 text-center text-mist", hideBelow && HIDE[hideBelow], className)}>
      {children}
    </td>
  );
}

function Legend({ className, label }: { className: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={cn("size-2.5 rounded-sm", className)} /> {label}
    </span>
  );
}

export function StandingsSkeleton() {
  return <PanelSkeleton className="h-[760px]" />;
}
