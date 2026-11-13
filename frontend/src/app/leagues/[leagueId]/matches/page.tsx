import type { Metadata } from "next";
import { Suspense } from "react";

import { MatchesView, MatchesViewSkeleton } from "@/features/fixtures/matches-view";

export const metadata: Metadata = { title: "Maçlar" };

export default function MatchesPage() {
  return (
    // Filtreler URL'den okunur → Suspense içinde.
    <Suspense fallback={<MatchesViewSkeleton />}>
      <MatchesView />
    </Suspense>
  );
}
