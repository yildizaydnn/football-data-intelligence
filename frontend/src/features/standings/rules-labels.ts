import type { Rules, Zone } from "@/lib/api/types";

/** Kural adlarının arayüz metinleri (kuralların kendisi backend spec'inde). */
export const CRITERION_LABEL: Record<string, string> = {
  points: "puan",
  goal_difference: "averaj",
  goals_for: "atılan gol",
  goals_against: "yenilen gol",
  wins: "galibiyet",
  away_goals_for: "deplasman golü",
  h2h_points: "ikili puan",
  h2h_goal_difference: "ikili averaj",
  h2h_goals_for: "ikili maçlarda atılan gol",
  h2h_away_goals_for: "ikili maçlarda deplasman golü",
};

export const ZONE_STYLE: Record<Zone["kind"], { badge: string; swatch: string }> = {
  champions_league: { badge: "bg-lime text-pitch-900", swatch: "bg-lime" },
  europa_league: { badge: "bg-[#ff9f43] text-pitch-900", swatch: "bg-[#ff9f43]" },
  conference_league: { badge: "bg-pitch-500 text-chalk", swatch: "bg-pitch-500" },
  relegation_playoff: { badge: "bg-amber/30 text-[#ffd59a]", swatch: "bg-amber/70" },
  relegation: { badge: "bg-loss/25 text-[#ffb3a8]", swatch: "bg-loss/70" },
};

/** "Puan eşitliğinde: ikili puan → ikili averaj → …" (ilk kriter = puan, atlanır). */
export function tiebreakSentence(rules: Rules) {
  const steps = rules.tiebreakers
    .filter((name) => name !== "points")
    .map((name) => CRITERION_LABEL[name] ?? name);
  const note = rules.head_to_head_requires_all_matches && rules.tiebreakers.some((n) => n.startsWith("h2h_"))
    ? " (ikili kriterler karşılıklı maçların hepsi oynandıysa)"
    : "";
  return `Puan eşitliğinde: ${steps.join(" → ")}${note}`;
}

/** Aynı türden bölgeleri tekilleştirir (açıklama satırı için). */
export function legendZones(rules: Rules) {
  const seen = new Set<string>();
  return rules.zones.filter((z) => !seen.has(z.label) && seen.add(z.label));
}
