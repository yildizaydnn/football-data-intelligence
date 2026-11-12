"use client";

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { type ChartConfig, ChartContainer, ChartTooltip } from "@/components/ui/chart";
import type { TeamStats } from "@/lib/api/types";
import { Panel, PanelHeader } from "@/shared/components/panel";
import { formatDay } from "@/shared/lib/format";

const LAST = 10;
const config = {
  scored: { label: "Atılan", color: "var(--color-lime)" },
  conceded: { label: "Yenilen", color: "var(--color-loss)" },
} satisfies ChartConfig;

export function GoalsChart({ stats }: { stats: TeamStats }) {
  const data = stats.timeline.slice(-LAST).map((p) => ({
    score: `${p.goals_for}-${p.goals_against}`,
    scored: p.goals_for,
    conceded: p.goals_against,
    opponent: p.opponent.name,
    venue: p.is_home ? "İç saha" : "Deplasman",
    date: formatDay(p.kickoff_at),
  }));

  return (
    <Panel className="animate-fade-up">
      <PanelHeader
        title={`Son ${data.length} maç: atılan / yenilen`}
        aside={
          <span className="flex gap-4">
            <LegendDot className="bg-lime" label="Atılan" />
            <LegendDot className="bg-loss" label="Yenilen" />
          </span>
        }
      />
      <ChartContainer config={config} className="aspect-auto h-[240px] w-full">
        <BarChart data={data} margin={{ top: 8, left: 0, right: 0, bottom: 0 }} barGap={4}>
          <CartesianGrid vertical={false} stroke="rgb(255 255 255 / 6%)" />
          <XAxis dataKey="score" tickLine={false} axisLine={false} tickMargin={10} fontSize={11} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={11} width={32} />
          <ChartTooltip
            cursor={{ fill: "rgb(255 255 255 / 4%)" }}
            content={({ active, payload }) => {
              const d = payload?.[0]?.payload as (typeof data)[number] | undefined;
              if (!active || !d) return null;
              return (
                <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-lg">
                  <p className="font-semibold">
                    {d.venue} · {d.opponent}
                  </p>
                  <p className="text-sage">
                    {d.date} · {d.score}
                  </p>
                </div>
              );
            }}
          />
          <Bar dataKey="scored" fill="var(--color-scored)" radius={[5, 5, 0, 0]} maxBarSize={22} animationDuration={700} />
          <Bar dataKey="conceded" fill="var(--color-conceded)" radius={[5, 5, 0, 0]} maxBarSize={22} animationDuration={700} />
        </BarChart>
      </ChartContainer>
    </Panel>
  );
}

function LegendDot({ className, label }: { className: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`size-2.5 rounded-sm ${className}`} /> {label}
    </span>
  );
}
