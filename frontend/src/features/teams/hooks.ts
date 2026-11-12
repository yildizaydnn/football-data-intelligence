"use client";

import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";

import { endpoints } from "@/lib/api/endpoints";

export const teamsQuery = (leagueId: number, season?: number) =>
  queryOptions({
    queryKey: ["leagues", leagueId, "teams", season ?? "default"],
    queryFn: () => endpoints.teams({ leagueId, season }),
  });

export const useTeams = (leagueId: number, season?: number) =>
  useSuspenseQuery(teamsQuery(leagueId, season)).data;
