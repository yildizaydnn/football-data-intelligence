"use client";

import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";

import { endpoints } from "@/lib/api/endpoints";

export const overviewQuery = (leagueId: number, season?: number) =>
  queryOptions({
    queryKey: ["leagues", leagueId, "overview", season ?? "default"],
    queryFn: () => endpoints.overview({ leagueId, season }),
  });

export const useOverview = (leagueId: number, season?: number) =>
  useSuspenseQuery(overviewQuery(leagueId, season)).data;
