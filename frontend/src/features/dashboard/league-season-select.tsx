"use client";

import { useQueryClient } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";

import { SelectField } from "@/shared/components/select-field";
import { formatSeason } from "@/shared/lib/format";

import { seasonsQuery, useDashboardParams, useLeagues, useSeasons } from "./hooks";

export function LeagueSeasonSelect() {
  const router = useRouter();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const { leagueId, season, href } = useDashboardParams();
  const leagues = useLeagues();
  const seasons = useSeasons(leagueId);
  // URL'de sezon yoksa backend varsayılanı (verisi olan en güncel sezon) = listenin başı.
  const currentSeason = season ?? seasons[0]?.year;

  // Lig değişince aynı sekmede ve (yeni ligde verisi varsa) aynı sezonda kalınır.
  // Takım id'leri ligler arası anlamsız: takım analizinde yeni ligin liderine gidilir.
  const switchLeague = async (id: string) => {
    const section = pathname.split("/")[3];
    const path = section ? `/${section}` : "";
    const target = await queryClient.fetchQuery(seasonsQuery(Number(id)));
    const keepSeason = season !== undefined && target.some((s) => s.year === season);
    router.push(`/leagues/${id}${path}${keepSeason ? `?season=${season}` : ""}`);
  };

  // Aynı sayfada (takım analizinde aynı takımda) kalınır; takım o sezonda ligde değilse
  // sayfa bunu söyler ve takım seçiciyi gösterir.
  const switchSeason = (year: string) => {
    const path = pathname.replace(`/leagues/${leagueId}`, "");
    router.push(href(path, { season: year }));
  };

  return (
    <div className="flex gap-2.5">
      <SelectField
        label="Lig"
        className="w-64"
        value={String(leagueId)}
        onChange={switchLeague}
        options={leagues.map((l) => ({
          value: String(l.id),
          label: l.country ? `${l.name} (${countryTr(l.country)})` : l.name,
        }))}
      />
      <SelectField
        label="Sezon"
        className="w-28"
        value={currentSeason ? String(currentSeason) : ""}
        onChange={switchSeason}
        disabled={seasons.length < 2}
        options={seasons.map((s) => ({ value: String(s.year), label: formatSeason(s.year) }))}
      />
    </div>
  );
}

const COUNTRY_TR: Record<string, string> = {
  Turkey: "Türkiye",
  England: "İngiltere",
  Spain: "İspanya",
  Germany: "Almanya",
  Italy: "İtalya",
};
const countryTr = (country: string) => COUNTRY_TR[country] ?? country;
