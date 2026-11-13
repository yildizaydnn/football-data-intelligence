from app.analytics.comparison import compare_teams
from app.insights.grounding import unverified_numbers
from app.insights.prompt import build_facts, facts_hash, season_label
from tests.rules_helpers import points_table
from tests.unit.analytics_helpers import match

A, B, C = 1, 2, 3
NAMES = {A: "Alfa", B: "Beta", C: "Gama"}
MATCHES = [
    match(A, B, "2-1", week=1),
    match(B, A, "0-0", week=2),
    match(A, C, "3-0", week=3),
    match(C, B, "1-1", week=4),
]


def _facts():
    comparison = compare_teams(A, B, MATCHES, points_table())
    return comparison, build_facts(
        comparison, league="Lig", season=season_label(2024), team_a="Alfa", team_b="Beta",
        team_names=NAMES,
    )  # fmt: skip


def test_head_to_head_record() -> None:
    comparison, _ = _facts()
    h2h = comparison.head_to_head

    assert len(h2h.matches) == 2
    assert (h2h.team_a_wins, h2h.draws, h2h.team_b_wins) == (1, 1, 0)
    assert (h2h.team_a_goals, h2h.team_b_goals) == (2, 1)
    assert comparison.team_a.overall.points == 7
    assert comparison.team_b.overall.points == 2


def test_facts_contain_scores_and_form() -> None:
    _, facts = _facts()

    assert facts["sezon"] == "2024/25"
    assert facts["takim_a"]["son_5_mac_eskiden_yeniye"] == "G-B-G"
    assert facts["aralarindaki_maclar"]["skorlar"][0].endswith("Alfa 2-1 Beta")


def test_facts_hash_changes_only_with_data() -> None:
    _, facts = _facts()
    _, same = _facts()
    changed = {**facts, "takim_a": {**facts["takim_a"], "puan": 99}}

    assert facts_hash(facts) == facts_hash(same)
    assert facts_hash(facts) != facts_hash(changed)


def test_grounding_accepts_data_numbers_and_differences() -> None:
    _, facts = _facts()
    text = (
        "Alfa 7 puanla Beta'nın (2) önünde, fark 5 puan. Alfa maç başına 1,67 gol attı; "
        "aralarındaki 2 maçta skor 2-1 ve 0-0 oldu. 2024/25 sezonunda."
    )

    assert unverified_numbers(text, facts) == []


def test_grounding_flags_invented_numbers() -> None:
    _, facts = _facts()

    assert unverified_numbers("Alfa 12 maçta 31 gol attı, %80 başarı.", facts) == ["12", "31", "80"]
