from datetime import date
from typing import Any

from pydantic import BaseModel

from app.providers.api_football.dto import FixtureDTO, LeagueDTO, TeamDTO
from app.providers.base import ProviderResponse
from tests.conftest import load_json


class FakeProvider:
    """FootballDataProvider'ın test dublörü. Varsayılan veriyi tests/fixtures/*.json'dan okur.

    `fixtures` listesi testte değiştirilerek API'deki güncellemeler simüle edilir;
    `fail_on` ile belirli bir çağrıda hata fırlatılabilir.
    """

    def __init__(self, remaining: int | None = 90) -> None:
        self.leagues: list[dict[str, Any]] = load_json("leagues.json")["response"]
        self.teams: list[dict[str, Any]] = load_json("teams.json")["response"]
        self.fixtures: list[dict[str, Any]] = load_json("fixtures.json")["response"]
        self.remaining = remaining
        self.calls: list[str] = []
        self.fail_on: dict[str, Exception] = {}

    def get_league(self, league_id: int) -> ProviderResponse[LeagueDTO]:
        data = [i for i in self.leagues if i["league"]["id"] == league_id]
        return self._respond("get_league", LeagueDTO, data)

    def get_teams(self, league_id: int, season: int) -> ProviderResponse[TeamDTO]:
        return self._respond("get_teams", TeamDTO, self.teams)

    def get_fixtures(
        self,
        league_id: int,
        season: int,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ProviderResponse[FixtureDTO]:
        return self._respond("get_fixtures", FixtureDTO, self.fixtures)

    def fixture(self, external_id: int) -> dict[str, Any]:
        return next(f for f in self.fixtures if f["fixture"]["id"] == external_id)

    def _respond[T: BaseModel](
        self, name: str, dto: type[T], data: list[dict[str, Any]]
    ) -> ProviderResponse[T]:
        self.calls.append(name)
        if name in self.fail_on:
            raise self.fail_on[name]
        if self.remaining is not None:
            self.remaining -= 1
        return ProviderResponse([dto.model_validate(i) for i in data], self.remaining)
