import type { TeamStats } from "@/lib/api/types";
import { AnimatedNumber } from "@/shared/components/animated-number";
import { FormStrip } from "@/shared/components/form-chip";
import { Panel } from "@/shared/components/panel";
import { formatDecimal } from "@/shared/lib/format";

const POINTS = { win: 3, draw: 1, loss: 0 } as const;
const STREAK_LABEL = { win: "galibiyet", draw: "beraberlik", loss: "mağlubiyet" } as const;

export function SummaryCards({ stats }: { stats: TeamStats }) {
  const { overall, recent, form, current_streak: streak } = stats;
  const formPoints = form.reduce((sum, r) => sum + POINTS[r], 0);

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Panel className="animate-fade-up">
        <h2 className="text-sm font-semibold text-mist">Son 5 maç (eski → yeni)</h2>
        <FormStrip form={form} size="lg" className="mt-4" />
        <p className="mt-4 text-sm text-sage">
          Son {form.length} maçta <b className="text-chalk">{formPoints} puan</b>
          {streak && streak.count > 1 && ` · ${streak.count} maçlık ${STREAK_LABEL[streak.result]} serisi`}
        </p>
      </Panel>

      <Panel className="animate-fade-up flex items-center gap-5" style={{ animationDelay: "0.05s" }}>
        <WinRateRing ratio={overall.win_rate} />
        <div>
          <h2 className="text-sm font-semibold text-mist">Galibiyet oranı</h2>
          <p className="mt-1.5 font-semibold">
            {overall.played} maçta {overall.won}G {overall.drawn}B {overall.lost}M
          </p>
          <p className="mt-1 text-sm text-sage">Maç başına {formatDecimal(overall.points_per_game)} puan</p>
          <RecentLine played={recent.played}>
            <Trend
              current={recent.win_rate}
              season={overall.win_rate}
              text={`%${Math.round(recent.win_rate * 100)}`}
            />
          </RecentLine>
        </div>
      </Panel>

      <Panel className="animate-fade-up" style={{ animationDelay: "0.1s" }}>
        <h2 className="text-sm font-semibold text-mist">Maç başına gol</h2>
        <div className="mt-3 flex gap-8">
          <Average value={overall.avg_goals_for} label="Atılan" className="text-lime" />
          <Average value={overall.avg_goals_against} label="Yenilen" className="text-loss" />
        </div>
        <p className="mt-3 text-sm text-sage">
          {overall.clean_sheets} maçta gol yemedi · {overall.failed_to_score} maçta gol atamadı
        </p>
        <RecentLine played={recent.played}>
          <Trend
            current={recent.avg_goals_for}
            season={overall.avg_goals_for}
            text={`${formatDecimal(recent.avg_goals_for)} attı`}
          />
          {" · "}
          <Trend
            current={recent.avg_goals_against}
            season={overall.avg_goals_against}
            text={`${formatDecimal(recent.avg_goals_against)} yedi`}
            lowerIsBetter
          />
        </RecentLine>
      </Panel>
    </div>
  );
}

/** Sezon geneli rakamların altında aynı metriğin son 5 maçtaki değeri. */
function RecentLine({ played, children }: { played: number; children: React.ReactNode }) {
  return (
    <p className="mt-2 border-t border-white/8 pt-2 text-sm text-sage">
      Son {played} maçta: {children}
    </p>
  );
}

/** Son maçlardaki değer sezon ortalamasından iyiyse yeşil ▲, kötüyse kırmızı ▼. */
function Trend({
  current,
  season,
  text,
  lowerIsBetter = false,
}: {
  current: number;
  season: number;
  text: string;
  lowerIsBetter?: boolean;
}) {
  const diff = current - season;
  if (Math.abs(diff) < 0.005) return <b className="text-chalk">{text}</b>;
  const better = lowerIsBetter ? diff < 0 : diff > 0;
  return (
    <b
      className={better ? "text-lime" : "text-loss"}
      title={better ? "Sezon ortalamasından iyi" : "Sezon ortalamasından kötü"}
    >
      {text} {diff > 0 ? "▲" : "▼"}
    </b>
  );
}

function Average({ value, label, className }: { value: number; label: string; className: string }) {
  return (
    <div>
      <div className={`font-display text-[46px] font-extrabold leading-none ${className}`}>
        <AnimatedNumber value={value} decimals={2} />
      </div>
      <div className="mt-1 text-sm text-sage">{label}</div>
    </div>
  );
}

const RADIUS = 42;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/** Halka çevreden hedef orana dolar (CSS animasyonu). */
function WinRateRing({ ratio }: { ratio: number }) {
  return (
    <div className="relative size-[104px] shrink-0">
      <svg viewBox="0 0 100 100" className="size-full -rotate-90" aria-hidden>
        <circle cx="50" cy="50" r={RADIUS} fill="none" stroke="rgb(255 255 255 / 8%)" strokeWidth="9" />
        <circle
          cx="50"
          cy="50"
          r={RADIUS}
          fill="none"
          stroke="var(--color-lime)"
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE * (1 - ratio)}
          className="animate-ring"
          style={{ "--ring-circumference": CIRCUMFERENCE } as React.CSSProperties}
        />
      </svg>
      <span className="font-display absolute inset-0 grid place-items-center text-3xl font-extrabold">
        <AnimatedNumber value={ratio * 100} format={(n) => `%${Math.round(n)}`} />
      </span>
    </div>
  );
}
