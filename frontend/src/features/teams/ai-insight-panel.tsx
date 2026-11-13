"use client";

import { CircleCheck, Sparkles, TriangleAlert } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useDashboardParams } from "@/features/dashboard/hooks";
import { ApiError } from "@/lib/api/client";
import type { Insight, TeamFacts } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { FootballIcon } from "@/shared/components/football-icon";
import { FormStrip } from "@/shared/components/form-chip";
import { Panel, PanelHeader } from "@/shared/components/panel";
import { SelectField } from "@/shared/components/select-field";
import { TeamCrest } from "@/shared/components/team-crest";
import { formatDateTime, formatDecimal, formatPercent } from "@/shared/lib/format";

import { useTeams } from "./hooks";
import { useAiStatus, useCreateInsight } from "./insight-hooks";

export function AiInsightPanel({ teamId }: { teamId: number }) {
  const { leagueId, season } = useDashboardParams();
  const status = useAiStatus();
  const teams = useTeams(leagueId, season).filter((t) => t.id !== teamId);
  const [opponent, setOpponent] = useState<string>("");
  const insight = useCreateInsight(leagueId, season);

  const run = () => insight.mutate({ teamAId: teamId, teamBId: Number(opponent) });

  return (
    <Panel className="animate-fade-up">
      <PanelHeader
        title={
          <span className="inline-flex items-center gap-2">
            <Sparkles className="size-5 text-lime" /> AI karşılaştırma
          </span>
        }
        aside={status.enabled ? `Bugün ${status.generated_today}/${status.daily_limit} analiz` : undefined}
      />
      {!status.enabled ? (
        <p className="text-sm text-sage">
          AI analizi yapılandırılmamış. Backend&apos;de <code className="text-mist">GEMINI_API_KEY</code>{" "}
          tanımlanınca etkinleşir.
        </p>
      ) : (
        <>
          <div className="flex flex-wrap items-end gap-3">
            <SelectField
              label="Rakip takım"
              className="w-full sm:w-64"
              value={opponent}
              onChange={setOpponent}
              options={teams.map((t) => ({ value: String(t.id), label: t.name }))}
            />
            <Button
              onClick={run}
              disabled={!opponent || insight.isPending}
              className="h-11 rounded-xl px-4 font-bold hover:bg-lime-bright"
            >
              {insight.isPending ? (
                <>
                  <FootballIcon className="animate-spin-ball size-[18px]" /> Analiz yazılıyor…
                </>
              ) : (
                <>
                  <Sparkles className="size-4" /> Analizi oluştur
                </>
              )}
            </Button>
          </div>
          <p className="mt-2 text-xs text-moss">
            Sayılar veritabanındaki maçlardan hesaplanır; yapay zekâ yalnızca yorumlar. Metindeki her
            sayı veriyle karşılaştırılır.
          </p>

          {insight.isPending && <Thinking />}
          {insight.error && <InsightError error={insight.error} />}
          {insight.data && !insight.isPending && (
            <InsightResult insight={orient(insight.data, teamId)} />
          )}
        </>
      )}
    </Panel>
  );
}

/** Backend çifti id sırasıyla döner; görüntülenen takım her zaman solda olsun. */
function orient(insight: Insight, teamId: number): Insight {
  if (insight.team_a.id === teamId) return insight;
  const h = insight.head_to_head;
  return {
    ...insight,
    team_a: insight.team_b,
    team_b: insight.team_a,
    team_a_facts: insight.team_b_facts,
    team_b_facts: insight.team_a_facts,
    head_to_head: {
      ...h,
      team_a_wins: h.team_b_wins,
      team_b_wins: h.team_a_wins,
      team_a_goals: h.team_b_goals,
      team_b_goals: h.team_a_goals,
    },
  };
}

function InsightResult({ insight }: { insight: Insight }) {
  const h2h = insight.head_to_head;
  const grounded = insight.unverified_numbers.length === 0;
  return (
    <div className="animate-fade-up mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
      <FactsTable insight={insight} />
      <div>
        <p className="leading-relaxed text-chalk">{insight.content}</p>
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs">
          {grounded ? (
            <span className="inline-flex items-center gap-1.5 text-win">
              <CircleCheck className="size-3.5" /> Metindeki tüm sayılar veriyle doğrulandı
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-amber">
              <TriangleAlert className="size-3.5" /> Veride bulunamayan sayılar:{" "}
              {insight.unverified_numbers.join(", ")}
            </span>
          )}
          <span className="text-moss">
            {insight.model} · {formatDateTime(insight.generated_at)}
            {insight.cached && " · önbellekten"}
          </span>
        </div>
        <p className="mt-3 text-xs text-sage">
          Aralarındaki maçlar: {h2h.matches} maç · {insight.team_a.name} {h2h.team_a_wins}G ·{" "}
          {h2h.draws}B · {insight.team_b.name} {h2h.team_b_wins}G · gol {h2h.team_a_goals}–
          {h2h.team_b_goals}
        </p>
      </div>
    </div>
  );
}

const ROWS: { label: string; value: (f: TeamFacts) => string; higherIsBetter?: boolean; raw: (f: TeamFacts) => number }[] = [
  { label: "Puan", value: (f) => String(f.points), raw: (f) => f.points, higherIsBetter: true },
  { label: "Galibiyet", value: (f) => formatPercent(f.win_rate), raw: (f) => f.win_rate, higherIsBetter: true },
  { label: "Atılan / maç", value: (f) => formatDecimal(f.avg_goals_for), raw: (f) => f.avg_goals_for, higherIsBetter: true },
  { label: "Yenilen / maç", value: (f) => formatDecimal(f.avg_goals_against), raw: (f) => f.avg_goals_against, higherIsBetter: false },
  { label: "İç saha puanı", value: (f) => String(f.home_points), raw: (f) => f.home_points, higherIsBetter: true },
  { label: "Deplasman puanı", value: (f) => String(f.away_points), raw: (f) => f.away_points, higherIsBetter: true },
];

function FactsTable({ insight }: { insight: Insight }) {
  const a = insight.team_a_facts;
  const b = insight.team_b_facts;
  const better = (row: (typeof ROWS)[number], side: "a" | "b") => {
    const [x, y] = side === "a" ? [row.raw(a), row.raw(b)] : [row.raw(b), row.raw(a)];
    return row.higherIsBetter ? x > y : x < y;
  };
  return (
    <div className="rounded-2xl border bg-pitch-900/50 p-4 text-sm">
      <div className="mb-3 grid grid-cols-[1fr_auto_1fr] items-center gap-2 text-xs font-semibold">
        <span className="flex min-w-0 items-center gap-2">
          <TeamCrest team={insight.team_a} size={20} />
          <span className="truncate">{insight.team_a.name}</span>
        </span>
        <span />
        <span className="flex min-w-0 items-center justify-end gap-2">
          <span className="truncate">{insight.team_b.name}</span>
          <TeamCrest team={insight.team_b} size={20} />
        </span>
      </div>
      <dl className="space-y-1.5">
        {ROWS.map((row) => (
          <div key={row.label} className="grid grid-cols-[1fr_auto_1fr] items-baseline gap-2">
            <dd className={cn("tabular", better(row, "a") ? "font-bold text-white" : "text-mist")}>
              {row.value(a)}
            </dd>
            <dt className="text-center text-xs text-sage">{row.label}</dt>
            <dd className={cn("tabular text-right", better(row, "b") ? "font-bold text-white" : "text-mist")}>
              {row.value(b)}
            </dd>
          </div>
        ))}
      </dl>
      <div className="mt-3 flex items-center justify-between gap-2 border-t pt-3">
        <FormStrip form={a.form} />
        <span className="text-xs text-sage">Son 5</span>
        <FormStrip form={b.form} />
      </div>
    </div>
  );
}

function Thinking() {
  return (
    <div className="mt-5 flex items-center gap-3 rounded-2xl border border-dashed border-white/10 p-4 text-sm text-sage">
      <FootballIcon className="animate-spin-ball size-5" />
      Veriler hazırlandı, yapay zekâ karşılaştırmayı yazıyor… (birkaç saniye sürebilir)
    </div>
  );
}

function InsightError({ error }: { error: Error }) {
  const message =
    error instanceof ApiError ? error.message : "Analiz oluşturulamadı, tekrar deneyin.";
  return (
    <p role="alert" className="mt-4 flex items-center gap-2 text-sm text-[#ffb3a8]">
      <TriangleAlert className="size-4" /> {message}
    </p>
  );
}
