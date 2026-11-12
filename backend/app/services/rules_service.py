from app.rules.engine import RuleEngine
from app.rules.models import RuleContext
from app.services.league_service import LeagueService


class RulesService:
    """Bir ligin (iç id) seçili sezonu için geçerli kuralları çözer."""

    def __init__(self, leagues: LeagueService, rules: RuleEngine) -> None:
        self.leagues = leagues
        self.rules = rules

    def get_rules(self, league_id: int, season_year: int | None = None) -> RuleContext:
        league = self.leagues.get_league(league_id)
        season = self.leagues.resolve_season(league_id, season_year)
        return self.rules.resolve(league.external_id, season.year)
