import type { Metadata } from "next";

import { TeamAnalysisSkeleton } from "@/features/teams/team-analysis-view";
import { TeamRedirect } from "@/features/teams/team-redirect";
import { QueryBoundary } from "@/shared/components/query-boundary";

export const metadata: Metadata = { title: "Takım Analizi" };

export default function TeamsPage() {
  return (
    <QueryBoundary fallback={<TeamAnalysisSkeleton />}>
      <TeamRedirect />
      <TeamAnalysisSkeleton />
    </QueryBoundary>
  );
}
