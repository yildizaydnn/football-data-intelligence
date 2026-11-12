import { OverviewSkeleton, OverviewView } from "@/features/overview/overview-view";
import { QueryBoundary } from "@/shared/components/query-boundary";

export default function OverviewPage() {
  return (
    <QueryBoundary fallback={<OverviewSkeleton />}>
      <OverviewView />
    </QueryBoundary>
  );
}
