"use client";

import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";

import { endpoints } from "@/lib/api/endpoints";

export const standingsQuery = (leagueId: number, season?: number) =>
  queryOptions({
    queryKey: ["leagues", leagueId, "standings", season ?? "default"],
    queryFn: () => endpoints.standings({ leagueId, season }),
  });

export const useStandings = (leagueId: number, season?: number) =>
  useSuspenseQuery(standingsQuery(leagueId, season)).data;
