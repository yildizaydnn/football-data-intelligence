"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useDashboardParams } from "@/features/dashboard/hooks";
import { useStandings } from "@/features/standings/hooks";
import { EmptyState } from "@/shared/components/states";

/** /teams → seçili sezonun lideri (takım seçiciden diğerlerine geçilir). */
export function TeamRedirect() {
  const router = useRouter();
  const { leagueId, season, href } = useDashboardParams();
  const leader = useStandings(leagueId, season).rows[0]?.team;
  const target = leader ? href(`/teams/${leader.id}`) : null;

  useEffect(() => {
    if (target) router.replace(target);
  }, [target, router]);

  return leader ? null : <EmptyState title="Bu sezon için henüz takım verisi yok" />;
}
