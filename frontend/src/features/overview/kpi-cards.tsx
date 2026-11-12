"use client";

import type { Overview } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { AnimatedNumber } from "@/shared/components/animated-number";
import { formatDay, formatDecimal, formatPercent, formatTime } from "@/shared/lib/format";

import { RUN_LABEL } from "@/features/sync/labels";

export function KpiCards({ overview }: { overview: Overview }) {
  const { summary, last_sync: lastSync } = overview;
  const s = summary.by_status;
  const pending = s.scheduled + s.live + s.postponed;
  const completion = summary.total_matches ? summary.finished / summary.total_matches : 0;

  const pendingParts = [
    s.live && `${s.live} canlı`,
    s.postponed && `${s.postponed} ertelendi`,
    `${s.scheduled} planlandı`,
    s.cancelled && `${s.cancelled} iptal`,
  ].filter(Boolean);

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Kpi label="Oynanan maç" delay={0}>
        <AnimatedNumber value={summary.finished} />
        <Note>
          Toplam {summary.total_matches} maç · {formatPercent(completion)} tamamlandı
        </Note>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/8">
          <div
            className="animate-grow-x h-full rounded-full bg-win"
            style={{ width: `${completion * 100}%` }}
          />
        </div>
      </Kpi>
      <Kpi label="Tamamlanmamış maç" delay={0.05}>
        <AnimatedNumber value={pending} />
        <Note>{pendingParts.join(" · ")}</Note>
      </Kpi>
      <Kpi label="Toplam gol" delay={0.1} accent>
        <AnimatedNumber value={summary.total_goals} />
        <Note>Maç başına {formatDecimal(summary.avg_goals_per_match)} gol</Note>
      </Kpi>
      <Kpi label="Son veri güncelleme" delay={0.15}>
        {lastSync ? (
          <>
            <span className="tabular">{formatTime(lastSync.finished_at ?? lastSync.started_at)}</span>
            <Note>
              <span
                className={cn("mr-1.5 inline-block size-2 rounded-full", RUN_LABEL[lastSync.status].dot)}
              />
              {formatDay(lastSync.started_at)} · {RUN_LABEL[lastSync.status].short}
            </Note>
          </>
        ) : (
          <>
            <span>—</span>
            <Note>Henüz senkronizasyon yapılmadı</Note>
          </>
        )}
      </Kpi>
    </div>
  );
}

function Kpi({
  label,
  delay,
  accent,
  children,
}: {
  label: string;
  delay: number;
  accent?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section
      className="animate-fade-up rounded-[20px] border bg-card p-5"
      style={{ animationDelay: `${delay}s` }}
    >
      <h2 className="text-sm font-semibold text-mist">{label}</h2>
      <div
        className={cn(
          "font-display mt-3 text-[46px] font-extrabold leading-none",
          accent && "text-lime",
        )}
      >
        {children}
      </div>
    </section>
  );
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="mt-2.5 font-sans text-sm font-normal text-sage">{children}</p>;
}
