"use client";

import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import { useParams, useSearchParams } from "next/navigation";
import { useCallback } from "react";

import { endpoints } from "@/lib/api/endpoints";

export const leaguesQuery = () =>
  queryOptions({ queryKey: ["leagues"], queryFn: endpoints.leagues, staleTime: Infinity });

export const seasonsQuery = (leagueId: number) =>
  queryOptions({
    queryKey: ["leagues", leagueId, "seasons"],
    queryFn: () => endpoints.seasons(leagueId),
  });

export const useLeagues = () => useSuspenseQuery(leaguesQuery()).data;
export const useSeasons = (leagueId: number) => useSuspenseQuery(seasonsQuery(leagueId)).data;

type Query = Record<string, string | number | undefined | null>;

/**
 * Lig ve sezon URL'den okunur (global state yok, link paylaşılabilir).
 * `href` sezonu koruyarak lig içi link üretir.
 */
export function useDashboardParams() {
  const params = useParams<{ leagueId: string; teamId?: string }>();
  const search = useSearchParams();
  const leagueId = Number(params.leagueId);
  const seasonParam = search.get("season");
  const season = seasonParam ? Number(seasonParam) : undefined;
  const teamId = params.teamId ? Number(params.teamId) : undefined;

  const href = useCallback(
    (path = "", query: Query = {}) => {
      const qs = new URLSearchParams();
      for (const [key, value] of Object.entries({ season, ...query })) {
        if (value != null && String(value) !== "") qs.set(key, String(value));
      }
      const suffix = qs.toString();
      return `/leagues/${leagueId}${path}${suffix ? `?${suffix}` : ""}`;
    },
    [leagueId, season],
  );

  return { leagueId, season, teamId, search, href };
}
