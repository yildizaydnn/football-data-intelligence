from datetime import date

from app.etl.transformers.league_transformer import LeagueTransformer, SeasonTransformer
from app.etl.transformers.team_transformer import TeamTransformer
from app.providers.api_football.dto import LeagueDTO, SeasonInfo, TeamDTO
from tests.conftest import load_json


def test_league_transformer() -> None:
    [dto] = [LeagueDTO.model_validate(i) for i in load_json("leagues.json")["response"]]

    assert LeagueTransformer().transform(dto) == {
        "external_id": 203,
        "name": "Süper Lig",
        "country": "Turkey",
        "logo_url": "https://media.api-sports.io/football/leagues/203.png",
    }


def test_season_transformer_parses_dates_and_tolerates_bad_ones() -> None:
    result = SeasonTransformer(league_id=1).transform_many(
        [
            SeasonInfo(year=2024, start="2024-08-09", end="2025-06-01", current=True),
            SeasonInfo(year=2023, start="bozuk", end=None),
            SeasonInfo(year=None),
        ]
    )

    assert [s["year"] for s in result.items] == [2024, 2023]
    assert result.items[0]["start_date"] == date(2024, 8, 9)
    assert result.items[1]["start_date"] is None
    assert len(result.skipped) == 1


def test_team_transformer() -> None:
    dtos = [TeamDTO.model_validate(i) for i in load_json("teams.json")["response"]]
    dtos.append(TeamDTO.model_validate({"team": {"id": 1, "name": "  "}}))

    result = TeamTransformer().transform_many(dtos)

    assert len(result.items) == 4
    assert result.items[0] == {
        "external_id": 645,
        "name": "Galatasaray",
        "code": "GAL",
        "logo_url": "https://media.api-sports.io/football/teams/645.png",
        "venue_name": "RAMS Park",
    }
    assert result.items[3]["code"] is None
    assert result.skipped[0].reason == "team.name eksik"
