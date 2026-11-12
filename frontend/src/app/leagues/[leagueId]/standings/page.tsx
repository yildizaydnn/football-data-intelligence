import type { Metadata } from "next";

import { StandingsSkeleton, StandingsTable } from "@/features/standings/standings-table";
import { QueryBoundary } from "@/shared/components/query-boundary";

export const metadata: Metadata = { title: "Puan Tablosu" };

export default function StandingsPage() {
  return (
    <QueryBoundary fallback={<StandingsSkeleton />}>
      <StandingsTable />
    </QueryBoundary>
  );
}
