"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { Fixture } from "@/lib/api/types";
import { FootballIcon } from "@/shared/components/football-icon";
import { EmptyState } from "@/shared/components/states";
import { dayKey, formatMatchDay } from "@/shared/lib/format";

import { type MatchFilters, useFixtures } from "./hooks";
import { MatchDetailDialog } from "./match-detail-dialog";
import { MatchRow } from "./match-row";

export function MatchList({ filters }: { filters: MatchFilters }) {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useFixtures(filters);
  const [openId, setOpenId] = useState<number | null>(null);

  const fixtures = data.pages.flatMap((page) => page.items);
  const total = data.pages[0]?.total ?? 0;

  if (fixtures.length === 0) {
    return (
      <EmptyState
        title="Bu filtrelere uyan maç yok"
        hint="Farklı bir takım, tarih aralığı ya da durum seçmeyi deneyin."
      />
    );
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-sage">
        <span className="tabular font-semibold text-chalk">{total}</span> maç
        {fixtures.length < total && ` · ${fixtures.length} gösteriliyor`}
      </p>

      {groupByDay(fixtures).map((group, i) => (
        <section
          key={group.key}
          className="animate-fade-up"
          style={{ animationDelay: `${Math.min(i, 8) * 0.04}s` }}
        >
          <h3 className="mb-2.5 text-xs font-bold uppercase tracking-[0.14em] text-mist">
            {formatMatchDay(group.items[0].kickoff_at)}
          </h3>
          <ul className="divide-y divide-white/7 overflow-hidden rounded-2xl border bg-card">
            {group.items.map((fixture) => (
              <MatchRow key={fixture.id} fixture={fixture} onOpen={() => setOpenId(fixture.id)} />
            ))}
          </ul>
        </section>
      ))}

      {hasNextPage && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="h-11 rounded-xl border-white/14 px-5"
          >
            {isFetchingNextPage ? (
              <>
                <FootballIcon className="animate-spin-ball size-4" /> Yükleniyor…
              </>
            ) : (
              `Daha fazla göster (${total - fixtures.length} maç daha)`
            )}
          </Button>
        </div>
      )}

      <MatchDetailDialog fixtureId={openId} onClose={() => setOpenId(null)} />
    </div>
  );
}

function groupByDay(fixtures: Fixture[]) {
  const groups: { key: string; items: Fixture[] }[] = [];
  for (const fixture of fixtures) {
    const key = dayKey(fixture.kickoff_at);
    const last = groups.at(-1);
    if (last?.key === key) last.items.push(fixture);
    else groups.push({ key, items: [fixture] });
  }
  return groups;
}
