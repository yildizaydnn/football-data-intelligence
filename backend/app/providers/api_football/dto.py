"""API-Football v3 ham yanıt modelleri.

Bilerek esnek tutuldu: alanların çoğu opsiyonel. Tek bir bozuk kayıt tüm yanıtın
parse edilmesini engellememeli; doğrulama ve atlama kararı ETL transformer'ında verilir.
"""

from pydantic import BaseModel, ConfigDict


class _DTO(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


# --- /leagues ---


class LeagueInfo(_DTO):
    id: int | None = None
    name: str | None = None
    type: str | None = None
    logo: str | None = None


class CountryInfo(_DTO):
    name: str | None = None
    code: str | None = None


class SeasonInfo(_DTO):
    year: int | None = None
    start: str | None = None  # "2024-08-09"
    end: str | None = None
    current: bool = False


class LeagueDTO(_DTO):
    league: LeagueInfo = LeagueInfo()
    country: CountryInfo = CountryInfo()
    seasons: list[SeasonInfo] = []


# --- /teams ---


class TeamInfo(_DTO):
    id: int | None = None
    name: str | None = None
    code: str | None = None
    logo: str | None = None


class VenueInfo(_DTO):
    name: str | None = None
    city: str | None = None


class TeamDTO(_DTO):
    team: TeamInfo = TeamInfo()
    venue: VenueInfo = VenueInfo()


# --- /fixtures ---


class FixtureStatus(_DTO):
    long: str | None = None
    short: str | None = None  # "NS", "1H", "FT", "PST"...
    elapsed: int | None = None


class FixtureInfo(_DTO):
    id: int | None = None
    date: str | None = None  # ISO 8601, ör. "2024-09-21T17:00:00+00:00"
    timestamp: int | None = None
    status: FixtureStatus = FixtureStatus()


class FixtureLeague(_DTO):
    id: int | None = None
    season: int | None = None
    round: str | None = None


class FixtureTeam(_DTO):
    id: int | None = None
    name: str | None = None
    logo: str | None = None


class FixtureTeams(_DTO):
    home: FixtureTeam = FixtureTeam()
    away: FixtureTeam = FixtureTeam()


class Goals(_DTO):
    home: int | None = None
    away: int | None = None


class FixtureDTO(_DTO):
    fixture: FixtureInfo = FixtureInfo()
    league: FixtureLeague = FixtureLeague()
    teams: FixtureTeams = FixtureTeams()
    goals: Goals = Goals()


# --- /fixtures/statistics ---


class StatisticItem(_DTO):
    type: str | None = None  # "Shots on Goal", "Ball Possession", "expected_goals"...
    value: int | float | str | None = None  # 9, "59%", "3.04" veya null


class TeamStatisticsDTO(_DTO):
    team: TeamInfo = TeamInfo()
    statistics: list[StatisticItem] = []
