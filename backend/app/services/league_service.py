from app.core.exceptions import NotFoundError
from app.models import League, Season
from app.repositories.league_repository import LeagueRepository, SeasonRepository


class LeagueService:
    def __init__(self, leagues: LeagueRepository, seasons: SeasonRepository) -> None:
        self.leagues = leagues
        self.seasons = seasons

    def list_leagues(self) -> list[League]:
        return self.leagues.list(order_by=[League.name])

    def get_league(self, league_id: int) -> League:
        league = self.leagues.get(league_id)
        if league is None:
            raise NotFoundError(f"Lig bulunamadı: {league_id}")
        return league

    def list_seasons(self, league_id: int) -> list[Season]:
        """Verisi yüklenmiş sezonlar. API tüm sezonları bildirir ama yalnızca bazıları sync edilir
        (ör. ücretsiz plan güncel sezona erişemez)."""
        self.get_league(league_id)
        return self.seasons.list_with_fixtures(league_id)

    def resolve_season(self, league_id: int, year: int | None = None) -> Season:
        """Yıl verilmezse: verisi olan güncel sezon, yoksa verisi olan en yeni sezon."""
        if year is not None:
            season = self.seasons.get_by_year(league_id, year)
            if season is None:
                raise NotFoundError(f"Sezon bulunamadı: lig={league_id}, yıl={year}")
            return season

        seasons = self.list_seasons(league_id)
        if not seasons:
            raise NotFoundError(f"Ligin verisi yüklenmiş sezonu yok: {league_id}")
        return next((s for s in seasons if s.is_current), seasons[0])
