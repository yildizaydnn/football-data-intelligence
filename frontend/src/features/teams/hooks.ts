"use client";

import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";

export const teamsQuery = (leagueId: number, season?: number) =>
  queryOptions({
    queryKey: ["leagues", leagueId, "teams", season ?? "default"],
    queryFn: () => endpoints.teams({ leagueId, season }),
  });

export const useTeams = (leagueId: number, season?: number) =>
  useSuspenseQuery(teamsQuery(leagueId, season)).data;

export const teamStatsQuery = (leagueId: number, teamId: number, season?: number) =>
  queryOptions({
    queryKey: ["leagues", leagueId, "teams", teamId, "stats", season ?? "default"],
    // 404: takım bu lig/sezonda yok (ör. sezon değişince küme düşmüş takım). Hata değil, boş durum.
    queryFn: () =>
      endpoints.teamStats({ leagueId, teamId, season }).catch((error: unknown) => {
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }),
  });

export const useTeamStats = (leagueId: number, teamId: number, season?: number) =>
  useSuspenseQuery(teamStatsQuery(leagueId, teamId, season)).data;
