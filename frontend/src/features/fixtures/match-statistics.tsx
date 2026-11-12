"use client";

import { BarChart3, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import type { FixtureDetail, StatLine } from "@/lib/api/types";
import { formatDecimal } from "@/shared/lib/format";

import { useFixtureStatistics } from "./hooks";

/** Anahtarların arayüz metinleri; anahtarlar ve sıraları backend kural spec'inden gelir. */
const LABEL: Record<string, string> = {
  possession: "Topa sahip olma",
  expected_goals: "Gol beklentisi (xG)",
  total_shots: "Toplam şut",
  shots_on_goal: "İsabetli şut",
  shots_off_goal: "İsabetsiz şut",
  blocked_shots: "Engellenen şut",
  shots_inside_box: "Ceza sahası içinden şut",
  shots_outside_box: "Ceza sahası dışından şut",
  corner_kicks: "Korner",
  offsides: "Ofsayt",
  fouls: "Faul",
  yellow_cards: "Sarı kart",
  red_cards: "Kırmızı kart",
  goalkeeper_saves: "Kaleci kurtarışı",
  total_passes: "Toplam pas",
  passes_accurate: "İsabetli pas",
  pass_accuracy: "Pas isabeti",
};
const PERCENT = new Set(["possession", "pass_accuracy"]);
const DECIMAL = new Set(["expected_goals"]);

export function MatchStatistics({ fixture }: { fixture: FixtureDetail }) {
  const finished = fixture.status === "finished";
  const { data, error, isPending, refetch, isRefetching } = useFixtureStatistics(fixture.id, finished);

  return (
    <section className="border-t pt-4">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
        <BarChart3 className="size-4 text-sage" /> Maç istatistikleri
      </h3>
      {!finished ? (
        <Note>İstatistikler maç bittiğinde çekilir.</Note>
      ) : error ? (
        <StatisticsError error={error} onRetry={() => refetch()} retrying={isRefetching} />
      ) : isPending ? (
        <div className="space-y-2.5">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-6 rounded-md bg-pitch-800" />
          ))}
        </div>
      ) : data.availability !== "available" ? (
        <Note>Veri sağlayıcı bu maç için istatistik sunmuyor.</Note>
      ) : (
        <>
          <div className="mb-2 flex justify-between text-xs font-semibold text-mist">
            <span className="truncate">{fixture.home_team.name}</span>
            <span className="truncate">{fixture.away_team.name}</span>
          </div>
          <ul className="max-h-[38vh] space-y-3 overflow-y-auto pr-1">
            {data.lines.map((line, i) => (
              <StatRow key={line.key} line={line} delay={i * 0.03} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function StatRow({ line, delay }: { line: StatLine; delay: number }) {
  const home = line.home ?? 0;
  const away = line.away ?? 0;
  const total = home + away;
  const homeShare = total > 0 ? home / total : 0.5;
  const homeLeads = home > away;
  const awayLeads = away > home;

  return (
    <li className="animate-fade-up" style={{ animationDelay: `${delay}s` }}>
      <div className="flex items-baseline justify-between text-sm">
        <span className={homeLeads ? "font-bold text-white" : "text-mist"}>{show(line.key, line.home)}</span>
        <span className="text-xs text-sage">{LABEL[line.key] ?? line.key}</span>
        <span className={awayLeads ? "font-bold text-white" : "text-mist"}>{show(line.key, line.away)}</span>
      </div>
      <div className="mt-1.5 flex h-1.5 gap-1" aria-hidden>
        <div className="flex flex-1 justify-end overflow-hidden rounded-full bg-white/6">
          <span
            className={`animate-grow-x h-full rounded-full [transform-origin:right] ${homeLeads ? "bg-lime" : "bg-mist/50"}`}
            style={{ width: `${homeShare * 100}%`, animationDelay: `${delay}s` }}
          />
        </div>
        <div className="flex-1 overflow-hidden rounded-full bg-white/6">
          <span
            className={`animate-grow-x block h-full rounded-full ${awayLeads ? "bg-lime" : "bg-mist/50"}`}
            style={{ width: `${(1 - homeShare) * 100}%`, animationDelay: `${delay}s` }}
          />
        </div>
      </div>
    </li>
  );
}

function show(key: string, value: number | null) {
  if (value === null) return "—";
  if (PERCENT.has(key)) return `%${Math.round(value)}`;
  if (DECIMAL.has(key)) return formatDecimal(value);
  return value.toLocaleString("tr-TR");
}

function StatisticsError({
  error,
  onRetry,
  retrying,
}: {
  error: Error;
  onRetry: () => void;
  retrying: boolean;
}) {
  const quota = error instanceof ApiError && error.status === 429;
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <Note>
        {quota
          ? error.message
          : "İstatistikler şu an alınamadı (veri sağlayıcıya ulaşılamadı)."}
      </Note>
      {!quota && (
        <Button variant="outline" size="sm" onClick={onRetry} disabled={retrying}>
          <RotateCcw /> Tekrar dene
        </Button>
      )}
    </div>
  );
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-sage">{children}</p>;
}
