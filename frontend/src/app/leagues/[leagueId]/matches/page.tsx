import type { Metadata } from "next";

import { ComingSoon } from "@/shared/components/coming-soon";

export const metadata: Metadata = { title: "Maçlar" };

export default function MatchesPage() {
  return <ComingSoon title="Maçlar" />;
}
