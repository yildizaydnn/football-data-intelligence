import { DashboardShell, DashboardShellSkeleton } from "@/features/dashboard/dashboard-shell";
import { QueryBoundary } from "@/shared/components/query-boundary";

// Çerçeve lig/sezonu URL'den okur; Cache Components ile bu kısım Suspense içinde olmalı
// (QueryBoundary Suspense + hata sınırını birlikte sağlar).
export default function LeagueLayout({ children }: LayoutProps<"/leagues/[leagueId]">) {
  return (
    <QueryBoundary fallback={<DashboardShellSkeleton />}>
      <DashboardShell>{children}</DashboardShell>
    </QueryBoundary>
  );
}
