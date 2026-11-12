import { RootRedirect } from "@/features/dashboard/root-redirect";
import { DashboardShellSkeleton } from "@/features/dashboard/dashboard-shell";
import { QueryBoundary } from "@/shared/components/query-boundary";

export default function Home() {
  return (
    <QueryBoundary fallback={<DashboardShellSkeleton />}>
      <RootRedirect />
      <DashboardShellSkeleton />
    </QueryBoundary>
  );
}
