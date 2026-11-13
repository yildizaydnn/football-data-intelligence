"use client";

import { notFound } from "next/navigation";

import { useDashboardParams, useLeagues } from "./hooks";

/** URL'deki lig yoksa 404. Kendi sınırında çalışır; çerçeveyi ve sayfayı bekletmez. */
export function LeagueGuard() {
  const { leagueId } = useDashboardParams();
  const leagues = useLeagues();
  if (!leagues.some((league) => league.id === leagueId)) notFound();
  return null;
}
