"use client";

import { Bar, BarChart, Cell, LabelList, XAxis } from "recharts";

import { type ChartConfig, ChartContainer, ChartTooltip } from "@/components/ui/chart";
import type { RoundGoals } from "@/lib/api/types";
import { EmptyState } from "@/shared/components/states";
import { Panel, PanelHeader } from "@/shared/components/panel";

const config = { goals: { label: "Gol", color: "var(--color-pitch-500)" } } satisfies ChartConfig;

export function GoalsByRoundChart({ rounds }: { rounds: RoundGoals[] }) {
  if (rounds.length === 0) {
    return (
      <Panel>
        <PanelHeader title="Haftalara göre gol" />
        <EmptyState title="Henüz oynanmış hafta yok" />
      </Panel>
    );
  }

  const data = rounds.map((r, i) => ({ ...r, label: r.number ? `${r.number}.` : `#${i + 1}` }));
  const best = data.reduce((a, b) => (b.goals > a.goals ? b : a));
  const dense = data.length > 20; // 38 haftada etiketler sıkışmasın

  return (
    <Panel className="animate-fade-up">
      <PanelHeader
        title="Haftalara göre gol"
        aside={`En golcü hafta: ${best.label} hafta (${best.goals} gol)`}
      />
      <ChartContainer config={config} className="aspect-auto h-[240px] w-full">
        <BarChart data={data} margin={{ top: 22, left: 0, right: 0, bottom: 0 }}>
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={{ stroke: "rgb(255 255 255 / 10%)" }}
            tickMargin={8}
            interval={dense ? "preserveStartEnd" : 0}
            minTickGap={6}
            fontSize={11}
          />
          <ChartTooltip
            cursor={{ fill: "rgb(255 255 255 / 4%)" }}
            content={({ active, payload }) => {
              const item = payload?.[0]?.payload as (typeof data)[number] | undefined;
              if (!active || !item) return null;
              return (
                <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-lg">
                  <p className="font-semibold">{item.label} hafta</p>
                  <p className="text-sage">
                    {item.goals} gol · {item.matches} maç
                  </p>
                </div>
              );
            }}
          />
          <Bar dataKey="goals" radius={[6, 6, 2, 2]} animationDuration={700} maxBarSize={44}>
            {data.map((d) => (
              <Cell key={d.round} fill={d === best ? "var(--color-lime)" : "var(--color-goals)"} />
            ))}
            <LabelList
              dataKey="goals"
              position="top"
              offset={6}
              // Dar ekranda değerler tooltip'te; çubuk üstü etiketler sıkışmasın.
              className={dense ? "fill-chalk font-semibold max-md:hidden" : "fill-chalk font-semibold"}
              fontSize={dense ? 9 : 12}
            />
          </Bar>
        </BarChart>
      </ChartContainer>
    </Panel>
  );
}
