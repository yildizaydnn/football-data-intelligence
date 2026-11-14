"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { EmptyState } from "@/shared/components/states";

import { useLeagues } from "./hooks";

const DEFAULT_LEAGUE_EXTERNAL_ID = 203; // Süper Lig (API-Football id)

/** "/" → Süper Lig, yüklü değilse ilk lig. Hiç lig yoksa veri yüklenmesi gerektiğini söyler. */
export function RootRedirect() {
  const router = useRouter();
  const leagues = useLeagues();
  const first =
    leagues.find((league) => league.external_id === DEFAULT_LEAGUE_EXTERNAL_ID) ?? leagues[0];

  useEffect(() => {
    if (first) router.replace(`/leagues/${first.id}`);
  }, [first, router]);

  if (!first) {
    return (
      <EmptyState
        title="Henüz veri yok"
        hint="Backend'de `make sync` ile ilk veri yüklemesini yapın, sonra sayfayı yenileyin."
      />
    );
  }
  return null;
}
