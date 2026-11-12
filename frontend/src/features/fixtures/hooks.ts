"use client";

import {
  infiniteQueryOptions,
  queryOptions,
  useQuery,
  useSuspenseInfiniteQuery,
} from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { useCallback } from "react";

import { useDashboardParams } from "@/features/dashboard/hooks";
import { endpoints, type FixtureQuery } from "@/lib/api/endpoints";
import type { MatchStatus } from "@/lib/api/types";

export const PAGE_SIZE = 40;
const STATUSES: MatchStatus[] = ["finished", "live", "scheduled", "postponed", "cancelled"];
/** Türkiye 2016'dan beri sabit UTC+3; gün sınırları Türkiye saatine göre. */
const TR_OFFSET = "+03:00";

export type MatchFilters = {
  teamId?: number;
  status?: MatchStatus;
  from?: string; // YYYY-MM-DD (dahil)
  to?: string; // YYYY-MM-DD (dahil)
  order: "asc" | "desc";
};

/** Filtreler URL'de: link paylaşılabilir, geri tuşu çalışır. */
export function useMatchFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const { search } = useDashboardParams();

  const status = search.get("status") as MatchStatus | null;
  const team = Number(search.get("team"));
  const filters: MatchFilters = {
    teamId: Number.isInteger(team) && team > 0 ? team : undefined,
    status: status && STATUSES.includes(status) ? status : undefined,
    from: search.get("from") ?? undefined,
    to: search.get("to") ?? undefined,
    order: search.get("order") === "asc" ? "asc" : "desc",
  };

  const setFilters = useCallback(
    (patch: Partial<Record<"team" | "status" | "from" | "to" | "order", string | undefined>>) => {
      const next = new URLSearchParams(search.toString());
      for (const [key, value] of Object.entries(patch)) {
        if (value) next.set(key, value);
        else next.delete(key);
      }
      const qs = next.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [router, pathname, search],
  );

  return { filters, setFilters };
}

function toQuery(leagueId: number, season: number | undefined, f: MatchFilters): FixtureQuery {
  return {
    leagueId,
    season,
    teamId: f.teamId,
    status: f.status,
    dateFrom: f.from ? `${f.from}T00:00:00${TR_OFFSET}` : undefined,
    // Backend'de bitiş hariç: seçilen günün ertesi gece yarısı.
    dateTo: f.to ? nextDay(f.to) : undefined,
    order: f.order,
  };
}

function nextDay(day: string) {
  const date = new Date(`${day}T00:00:00${TR_OFFSET}`);
  date.setUTCDate(date.getUTCDate() + 1);
  return date.toISOString();
}

export const fixturesQuery = (leagueId: number, season: number | undefined, f: MatchFilters) =>
  infiniteQueryOptions({
    queryKey: ["leagues", leagueId, "fixtures", season ?? "default", f],
    queryFn: ({ pageParam }) =>
      endpoints.fixtures({ ...toQuery(leagueId, season, f), limit: PAGE_SIZE, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (last) =>
      last.offset + last.items.length < last.total ? last.offset + last.items.length : undefined,
  });

export function useFixtures(filters: MatchFilters) {
  const { leagueId, season } = useDashboardParams();
  return useSuspenseInfiniteQuery(fixturesQuery(leagueId, season, filters));
}

export const fixtureDetailQuery = (fixtureId: number) =>
  queryOptions({
    queryKey: ["fixtures", fixtureId],
    queryFn: () => endpoints.fixture(fixtureId),
  });

/** Dialog açıkken çekilir; dialog kendi yüklenme durumunu gösterir. */
export const useFixtureDetail = (fixtureId: number | null) =>
  useQuery({ ...fixtureDetailQuery(fixtureId ?? 0), enabled: fixtureId !== null });
