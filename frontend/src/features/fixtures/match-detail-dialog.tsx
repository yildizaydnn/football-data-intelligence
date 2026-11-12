"use client";

import { History } from "lucide-react";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import type { FixtureDetail, MatchStatus } from "@/lib/api/types";
import { ErrorState } from "@/shared/components/states";
import { STATUS_LABEL, StatusBadge } from "@/shared/components/status-badge";
import { TeamCrest } from "@/shared/components/team-crest";
import { formatDateTime, formatMatchDay, formatTime } from "@/shared/lib/format";

import { useFixtureDetail } from "./hooks";

export function MatchDetailDialog({ fixtureId, onClose }: { fixtureId: number | null; onClose: () => void }) {
  const { data, error, isPending, refetch } = useFixtureDetail(fixtureId);

  return (
    <Dialog open={fixtureId !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg rounded-[20px] border bg-card sm:max-w-lg">
        {error ? (
          <>
            <DialogTitle className="sr-only">Maç detayı</DialogTitle>
            <ErrorState error={error} onRetry={() => refetch()} />
          </>
        ) : isPending || !data ? (
          <>
            <DialogTitle className="sr-only">Maç detayı yükleniyor</DialogTitle>
            <Skeleton className="h-40 rounded-xl bg-pitch-800" />
          </>
        ) : (
          <FixtureDetailView fixture={data} />
        )}
      </DialogContent>
    </Dialog>
  );
}

function FixtureDetailView({ fixture }: { fixture: FixtureDetail }) {
  const scored = fixture.home_goals !== null && fixture.away_goals !== null;
  return (
    <>
      <DialogHeader>
        <DialogTitle className="sr-only">
          {fixture.home_team.name} - {fixture.away_team.name}
        </DialogTitle>
        <DialogDescription className="flex flex-wrap items-center justify-between gap-2 text-sage">
          <span>
            {formatMatchDay(fixture.kickoff_at)} · {formatTime(fixture.kickoff_at)}
            {fixture.round && ` · ${fixture.round.replace("Regular Season - ", "")}. hafta`}
          </span>
          <StatusBadge status={fixture.status} />
        </DialogDescription>
      </DialogHeader>

      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 py-4">
        <TeamBlock team={fixture.home_team} />
        <span className="font-display tabular text-5xl font-extrabold">
          {scored ? `${fixture.home_goals} – ${fixture.away_goals}` : "vs"}
        </span>
        <TeamBlock team={fixture.away_team} />
      </div>

      <section className="border-t pt-4">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <History className="size-4 text-sage" /> Veri güncelleme geçmişi
        </h3>
        {fixture.changes.length === 0 ? (
          <p className="text-sm text-sage">
            Bu maç için kayıtlı değişiklik yok. Skor, durum veya saat sonraki senkronizasyonlarda
            değişirse burada listelenir.
          </p>
        ) : (
          <ol className="space-y-2 text-sm">
            {fixture.changes.map((change, i) => (
              <li key={i} className="flex flex-wrap items-baseline justify-between gap-x-3">
                <span>
                  <span className="text-sage">{FIELD_LABEL[change.field] ?? change.field}:</span>{" "}
                  <span className="text-moss line-through">{show(change.field, change.old_value)}</span>{" "}
                  → <span className="font-semibold">{show(change.field, change.new_value)}</span>
                </span>
                <time className="text-xs text-moss" dateTime={change.changed_at}>
                  {formatDateTime(change.changed_at)}
                </time>
              </li>
            ))}
          </ol>
        )}
      </section>
    </>
  );
}

function TeamBlock({ team }: { team: FixtureDetail["home_team"] }) {
  return (
    <div className="flex flex-col items-center gap-2 text-center">
      <TeamCrest team={team} size={48} />
      <span className="text-sm font-semibold">{team.name}</span>
    </div>
  );
}

const FIELD_LABEL: Record<string, string> = {
  status: "Durum",
  home_goals: "Ev sahibi gol",
  away_goals: "Deplasman gol",
  kickoff_at: "Başlama saati",
};

function show(field: string, value: string | null) {
  if (value === null) return "—";
  if (field === "status") return STATUS_LABEL[value as MatchStatus] ?? value;
  if (field === "kickoff_at") return formatDateTime(value);
  return value;
}
