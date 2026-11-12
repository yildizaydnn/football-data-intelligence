import type { Metadata } from "next";

import { TeamAnalysisSkeleton, TeamAnalysisView } from "@/features/teams/team-analysis-view";
import { QueryBoundary } from "@/shared/components/query-boundary";

export const metadata: Metadata = { title: "Takım Analizi" };

export default function TeamPage() {
  return (
    <QueryBoundary fallback={<TeamAnalysisSkeleton />}>
      <TeamAnalysisView />
    </QueryBoundary>
  );
}
