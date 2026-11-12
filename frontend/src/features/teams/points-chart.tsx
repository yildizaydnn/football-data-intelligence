"use client";

import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { type ChartConfig, ChartContainer, ChartTooltip } from "@/components/ui/chart";
import type { TeamStats } from "@/lib/api/types";
import { Panel, PanelHeader } from "@/shared/components/panel";
import { formatDay } from "@/shared/lib/format";

const config = { points: { label: "Puan", color: "var(--color-lime)" } } satisfies ChartConfig;
const RESULT = { win: "G", draw: "B", loss: "M" } as const;

/** Sezon boyunca maç maç biriken puan. */
export function PointsChart({ stats }: { stats: TeamStats }) {
  const data = stats.timeline.map((p, i) => ({
    match: i + 1,
    points: p.cumulative_points,
    label: `${p.is_home ? "İç saha" : "Deplasman"} · ${p.opponent.name}`,
    detail: `${formatDay(p.kickoff_at)} · ${p.goals_for}-${p.goals_against} ${RESULT[p.result]}`,
  }));

  return (
    <Panel className="animate-fade-up">
      <PanelHeader title="Sezon boyu puan" aside={`${data.length} maçta ${data.at(-1)?.points ?? 0} puan`} />
      <ChartContainer config={config} className="aspect-auto h-[240px] w-full">
        <AreaChart data={data} margin={{ top: 8, left: 0, right: 4, bottom: 0 }}>
          <defs>
            <linearGradient id="points-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-points)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--color-points)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="rgb(255 255 255 / 6%)" />
          <XAxis
            dataKey="match"
            tickLine={false}
            axisLine={false}
            tickMargin={10}
            fontSize={11}
            interval="preserveStartEnd"
            minTickGap={16}
            tickFormatter={(m) => `${m}.`}
          />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={11} width={32} />
          <ChartTooltip
            cursor={{ stroke: "rgb(255 255 255 / 20%)" }}
            content={({ active, payload }) => {
              const d = payload?.[0]?.payload as (typeof data)[number] | undefined;
              if (!active || !d) return null;
              return (
                <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-lg">
                  <p className="font-semibold">
                    {d.match}. maç · {d.points} puan
                  </p>
                  <p className="text-sage">{d.label}</p>
                  <p className="text-sage">{d.detail}</p>
                </div>
              );
            }}
          />
          <Area
            type="monotone"
            dataKey="points"
            stroke="var(--color-points)"
            strokeWidth={2.5}
            fill="url(#points-fill)"
            animationDuration={900}
          />
        </AreaChart>
      </ChartContainer>
    </Panel>
  );
}
