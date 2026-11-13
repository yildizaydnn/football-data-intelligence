"""LLM'e gönderilecek veri ve talimat. Tüm sayılar analytics'ten gelir; LLM hesap yapmaz.

`build_facts` aynı zamanda önbellek anahtarının (facts hash) ve sayı doğrulamasının kaynağıdır.
"""

import hashlib
import json
from typing import Any

from app.analytics.comparison import TeamComparison
from app.analytics.team_performance import SplitStats, TeamPerformance

RESULT_TR = {"win": "G", "draw": "B", "loss": "M"}

SYSTEM_PROMPT = """Sen bir futbol veri analistisin.
Görevin iki takımı karşılaştıran kısa bir analiz yazmak.
Kurallar:
- Yalnızca kullanıcının verdiği JSON verisini kullan. Veride olmayan hiçbir sayı, oyuncu, teknik
  direktör, sakatlık, transfer, tarih ya da olaydan söz etme.
- Hesaplama yapma; sayıları verideki haliyle kullan (ondalık ayracı olarak virgül kullanabilirsin).
  Puan farkı gibi iki değerin farkını belirtmek serbest.
- Bahis tavsiyesi ya da kesin tahmin verme.
- Türkçe, akıcı, 4-6 cümlelik tek paragraf yaz. Başlık, madde işareti veya markdown kullanma."""


def build_facts(
    comparison: TeamComparison,
    *,
    league: str,
    season: str,
    team_a: str,
    team_b: str,
    team_names: dict[int, str],
) -> dict[str, Any]:
    h2h = comparison.head_to_head
    return {
        "lig": league,
        "sezon": season,
        "takim_a": _team(team_a, comparison.team_a),
        "takim_b": _team(team_b, comparison.team_b),
        "aralarindaki_maclar": {
            "mac": len(h2h.matches),
            f"{team_a}_galibiyet": h2h.team_a_wins,
            "beraberlik": h2h.draws,
            f"{team_b}_galibiyet": h2h.team_b_wins,
            f"{team_a}_gol": h2h.team_a_goals,
            f"{team_b}_gol": h2h.team_b_goals,
            "skorlar": [
                f"{m.kickoff_at:%Y-%m-%d} {team_names[m.home_team_id]} {m.home_goals}-"
                f"{m.away_goals} {team_names[m.away_team_id]}"
                for m in h2h.matches
            ],
        },
    }


def _team(name: str, perf: TeamPerformance) -> dict[str, Any]:
    o = perf.overall
    streak = perf.current_streak
    return {
        "ad": name,
        "mac": o.played,
        "puan": o.points,
        "galibiyet": o.won,
        "beraberlik": o.drawn,
        "maglubiyet": o.lost,
        "galibiyet_orani_yuzde": round(o.win_rate * 100),
        "atilan_gol": o.goals_for,
        "yenilen_gol": o.goals_against,
        "mac_basi_atilan": round(o.avg_goals_for, 2),
        "mac_basi_yenilen": round(o.avg_goals_against, 2),
        "gol_yemeden_biten_mac": o.clean_sheets,
        "son_5_mac_eskiden_yeniye": "-".join(RESULT_TR[r.value] for r in perf.form),
        "devam_eden_seri": f"{streak[1]} maç {RESULT_TR[streak[0].value]}" if streak else None,
        "ic_saha": _split(perf.home),
        "deplasman": _split(perf.away),
    }


def _split(s: SplitStats) -> dict[str, Any]:
    return {
        "mac": s.played,
        "puan": s.points,
        "galibiyet": s.won,
        "beraberlik": s.drawn,
        "maglubiyet": s.lost,
        "atilan_gol": s.goals_for,
        "yenilen_gol": s.goals_against,
    }


def season_label(year: int) -> str:
    """2024 → "2024/25" (API-Football sezonu başladığı yılla adlandırır)."""
    return f"{year}/{(year + 1) % 100:02d}"


def build_prompt(facts: dict[str, Any]) -> str:
    return (
        f"{facts['lig']} {facts['sezon']} sezonu için {facts['takim_a']['ad']} ve "
        f"{facts['takim_b']['ad']} takımlarını karşılaştır: genel performans ve form, gol üretimi "
        "ve savunma, iç saha/deplasman farkı, kendi aralarındaki maçlar.\n\nVeri:\n"
        f"```json\n{json.dumps(facts, ensure_ascii=False, indent=1)}\n```"
    )


def facts_hash(facts: dict[str, Any]) -> str:
    """Veri değişmedikçe aynı kalır; önbellek bununla geçersiz kılınır."""
    canonical = json.dumps(facts, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
