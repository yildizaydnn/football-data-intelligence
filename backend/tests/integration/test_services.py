from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import MatchResult, MatchStatus, SyncTrigger
from app.core.exceptions import NotFoundError
from app.models import League
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.league_repository import LeagueRepository, SeasonRepository
from app.repositories.sync_repository import SyncRunRepository
from app.repositories.team_repository import TeamRepository
from app.services.fixture_service import FixtureFilters, FixtureService
from app.services.league_service import LeagueService
from app.services.overview_service import OverviewService
from app.services.standings_service import StandingsService
from app.services.sync_service import SyncService
from app.services.team_stats_service import TeamStatsService
from tests.fakes import FakeProvider

SETTINGS = Settings(_env_file=None, default_league_id=203, default_season=2024)


@pytest.fixture
def league(db_session: Session) -> League:
    """Örnek veriyi gerçek sync akışıyla yükler (FakeProvider üzerinden)."""
    SyncService(db_session, FakeProvider(), SETTINGS).run(SyncTrigger.INITIAL)
    return LeagueRepository(db_session).get_by_external_id(203)


@pytest.fixture
def leagues(db_session: Session) -> LeagueService:
    return LeagueService(LeagueRepository(db_session), SeasonRepository(db_session))


@pytest.fixture
def standings(db_session: Session, leagues: LeagueService) -> StandingsService:
    return StandingsService(FixtureRepository(db_session), TeamRepository(db_session), leagues)


def _team_id(db_session: Session, external_id: int) -> int:
    return TeamRepository(db_session).get_by_external_id(external_id).id


class TestLeagueService:
    def test_resolves_current_season_by_default(self, league: League, leagues: LeagueService):
        assert leagues.resolve_season(league.id).year == 2024
        assert leagues.resolve_season(league.id, 2023).year == 2023

    def test_unknown_league_or_season_raises_not_found(self, league: League, leagues):
        with pytest.raises(NotFoundError):
            leagues.get_league(9999)
        with pytest.raises(NotFoundError):
            leagues.resolve_season(league.id, 1990)


class TestStandingsService:
    def test_standings_from_finished_matches(
        self, league: League, standings: StandingsService, db_session: Session
    ) -> None:
        result = standings.get_standings(league.id)

        # Bitenler: GS 1-3 FB, BJK 1-1 TS. Canlı (FB 2-0 BJK) sayılmaz.
        table = [(e.team.name, e.row.points, e.row.played) for e in result.entries]
        assert table == [
            ("Fenerbahçe", 3, 1),
            ("Beşiktaş", 1, 1),
            ("Trabzonspor", 1, 1),
            ("Galatasaray", 0, 1),
        ]
        assert result.season.year == 2024


class TestTeamStatsService:
    @pytest.fixture
    def service(self, db_session: Session, leagues: LeagueService) -> TeamStatsService:
        return TeamStatsService(FixtureRepository(db_session), TeamRepository(db_session), leagues)

    def test_team_stats(self, league: League, db_session: Session, service: TeamStatsService):
        fb_id = _team_id(db_session, 611)

        stats = service.get_team_stats(league.id, fb_id)

        assert stats.team.name == "Fenerbahçe"
        assert stats.performance.overall.played == 1
        assert stats.performance.away.won == 1
        assert stats.performance.form == [MatchResult.WIN]
        [point] = stats.performance.timeline
        assert stats.opponents[point.opponent_id].name == "Galatasaray"
        assert len(service.list_teams(league.id)) == 4

    def test_unknown_team(self, league: League, service: TeamStatsService):

        with pytest.raises(NotFoundError):
            service.get_team_stats(league.id, 9999)


class TestFixtureService:
    def test_list_with_filters_and_detail(
        self, league: League, db_session: Session, leagues: LeagueService
    ) -> None:
        service = FixtureService(FixtureRepository(db_session), leagues)

        page = service.list_fixtures(
            league.id, None, FixtureFilters(status=MatchStatus.FINISHED), limit=1
        )
        detail = service.get_fixture(page.items[0].id)

        assert (page.total, len(page.items)) == (2, 1)
        assert detail.fixture.home_team.name == "Galatasaray"
        assert detail.changes == []

    def test_missing_fixture(self, db_session: Session, leagues: LeagueService) -> None:
        with pytest.raises(NotFoundError):
            FixtureService(FixtureRepository(db_session), leagues).get_fixture(9999)


class TestOverviewService:
    def test_overview(
        self,
        league: League,
        db_session: Session,
        leagues: LeagueService,
        standings: StandingsService,
    ) -> None:
        service = OverviewService(
            FixtureRepository(db_session), SyncRunRepository(db_session), leagues, standings
        )

        overview = service.get_overview(league.id, now=datetime(2024, 10, 1, tzinfo=UTC))

        summary = overview.summary
        assert summary.total_matches == 5
        assert summary.by_status[MatchStatus.FINISHED] == 2
        assert summary.by_status[MatchStatus.LIVE] == 1
        assert (summary.total_goals, summary.avg_goals_per_match) == (6, 3.0)
        assert (summary.home_wins, summary.draws, summary.away_wins) == (0, 1, 1)
        assert overview.top_teams[0].team.name == "Fenerbahçe"
        assert [f.external_id for f in overview.recent_results] == [1002, 1001]
        assert [f.external_id for f in overview.upcoming] == [1004]  # 1005 ertelendi
        assert overview.last_sync is not None
