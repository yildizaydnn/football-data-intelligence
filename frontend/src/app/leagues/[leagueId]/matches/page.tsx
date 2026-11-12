import type { Metadata } from "next";

import { MatchesView } from "@/features/fixtures/matches-view";

export const metadata: Metadata = { title: "Maçlar" };

export default function MatchesPage() {
  return <MatchesView />;
}
