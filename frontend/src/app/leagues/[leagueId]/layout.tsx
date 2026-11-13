import { DashboardShell } from "@/features/dashboard/dashboard-shell";

// Çerçeve statiktir; URL/veri okuyan parçaları kendi Suspense sınırlarındadır.
export default function LeagueLayout({ children }: LayoutProps<"/leagues/[leagueId]">) {
  return <DashboardShell>{children}</DashboardShell>;
}
