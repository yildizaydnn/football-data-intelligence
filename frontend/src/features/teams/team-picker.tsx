"use client";

import { useRouter } from "next/navigation";

import { useDashboardParams } from "@/features/dashboard/hooks";
import { SelectField } from "@/shared/components/select-field";

import { useTeams } from "./hooks";

export function TeamPicker({ teamId }: { teamId: number }) {
  const router = useRouter();
  const { leagueId, season, href } = useDashboardParams();
  const teams = useTeams(leagueId, season);

  return (
    <SelectField
      label="Takım seç"
      className="w-full sm:w-60"
      value={String(teamId)}
      onChange={(id) => router.push(href(`/teams/${id}`))}
      options={teams.map((t) => ({ value: String(t.id), label: t.name }))}
    />
  );
}
