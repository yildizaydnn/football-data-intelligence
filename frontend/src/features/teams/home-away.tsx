import type { SplitStats, TeamStats } from "@/lib/api/types";
import { Panel, PanelHeader } from "@/shared/components/panel";
import { formatDecimal } from "@/shared/lib/format";

export function HomeAway({ stats }: { stats: TeamStats }) {
  return (
    <Panel className="animate-fade-up">
      <PanelHeader title="İç saha / deplasman" />
      <div className="space-y-6">
        <SplitRow label="İç saha" split={stats.home} delay={0} />
        <SplitRow label="Deplasman" split={stats.away} delay={0.1} />
      </div>
    </Panel>
  );
}

function SplitRow({ label, split, delay }: { label: string; split: SplitStats; delay: number }) {
  const parts = [
    { value: split.won, className: "bg-win" },
    { value: split.drawn, className: "bg-draw" },
    { value: split.lost, className: "bg-loss" },
  ];
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-semibold">{label}</span>
        <span className="text-sage">
          {split.points} puan · {split.played} maç
        </span>
      </div>
      <div
        className="animate-grow-x mt-2 flex h-2.5 gap-0.5 overflow-hidden rounded-full bg-white/8"
        style={{ animationDelay: `${delay}s` }}
        aria-label={`${split.won} galibiyet, ${split.drawn} beraberlik, ${split.lost} mağlubiyet`}
      >
        {split.played > 0 &&
          parts.map((p, i) =>
            p.value ? (
              <span key={i} className={p.className} style={{ width: `${(p.value / split.played) * 100}%` }} />
            ) : null,
          )}
      </div>
      <div className="mt-2 flex justify-between text-xs text-sage">
        <span className="tabular">
          <b className="text-win">{split.won}G</b> · {split.drawn}B · <b className="text-loss">{split.lost}M</b>
        </span>
        <span className="tabular">
          Gol {split.goals_for}–{split.goals_against} · maç başı {formatDecimal(split.avg_goals_for, 1)}–
          {formatDecimal(split.avg_goals_against, 1)}
        </span>
      </div>
    </div>
  );
}
