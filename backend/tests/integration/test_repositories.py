from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.enums import MatchStatus, SortOrder, SyncStatus, SyncTrigger
from app.models import Team
from app.repositories.api_usage_repository import ApiUsageRepository
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.league_repository import SeasonRepository
from app.repositories.sync_repository import SyncRunRepository
from app.repositories.team_repository import TeamRepository
from tests.integration.conftest import Seed

DAY = date(2024, 9, 21)


class TestSyncRunRepository:
    def test_second_running_sync_is_rejected(self, db_session: Session) -> None:
        repo = SyncRunRepository(db_session)

        first = repo.try_start(SyncTrigger.MANUAL)
        second = repo.try_start(SyncTrigger.SCHEDULED)

        assert first is not None and first.status is SyncStatus.RUNNING
        assert second is None
        assert repo.get_running() == first

    def test_finished_run_releases_lock(self, db_session: Session) -> None:
        repo = SyncRunRepository(db_session)
        run = repo.try_start(SyncTrigger.MANUAL)

        repo.finish(run, SyncStatus.SUCCESS, requests_made=2, inserted=10)

        assert run.finished_at is not None
        assert repo.get_running() is None
        assert repo.try_start(SyncTrigger.MANUAL) is not None

    def test_stale_run_is_failed(self, db_session: Session) -> None:
        repo = SyncRunRepository(db_session)
        run = repo.try_start(SyncTrigger.MANUAL)

        count = repo.fail_stale(older_than=timedelta(minutes=-1))  # "1 dk sonrasından eski"
        db_session.refresh(run)

        assert count == 1
        assert run.status is SyncStatus.FAILED


class TestApiUsageRepository:
    def test_budget_is_full_when_no_usage(self, db_session: Session) -> None:
        assert ApiUsageRepository(db_session).remaining_budget(100, day=DAY) == 100

    def test_record_accumulates_requests(self, db_session: Session) -> None:
        repo = ApiUsageRepository(db_session)

        repo.record(3, daily_limit=100, remaining=97, day=DAY)
        usage = repo.record(2, daily_limit=100, day=DAY)

        assert usage.requests_used == 5
        assert usage.remaining == 97  # header gelmediyse son bilinen değer korunur
        assert repo.remaining_budget(100, day=DAY) == 95

    def test_budget_uses_header_when_lower(self, db_session: Session) -> None:
        # Anahtar başka yerde de kullanılmış: API bizim sayacımızdan daha az hak bildiriyor.
        repo = ApiUsageRepository(db_session)
        repo.record(5, daily_limit=100, remaining=40, day=DAY)

        assert repo.remaining_budget(100, day=DAY) == 40

    def test_budget_never_negative(self, db_session: Session) -> None:
        repo = ApiUsageRepository(db_session)
        repo.record(120, daily_limit=100, day=DAY)

        assert repo.remaining_budget(100, day=DAY) == 0


class TestQueries:
    def test_list_filtered_by_team_and_status(self, db_session: Session, seed: Seed) -> None:
        other = Team(external_id=549, name="Beşiktaş")
        db_session.add(other)
        db_session.flush()
        repo = FixtureRepository(db_session)
        repo.upsert(
            [
                seed.fixture_item(1, status=MatchStatus.FINISHED, home_goals=1, away_goals=0),
                seed.fixture_item(2, home_team_id=other.id),
                seed.fixture_item(3, home_team_id=other.id, away_team_id=seed.home.id),
            ]
        )

        items, total = repo.list_filtered(seed.season.id, team_id=seed.away.id)
        finished = repo.list_finished(seed.season.id)

        assert total == 2
        assert {f.external_id for f in items} == {1, 2}
        assert items[0].home_team.name  # takımlar eager yüklenir
        assert [f.external_id for f in finished] == [1]

    def test_list_filtered_paginates(self, db_session: Session, seed: Seed) -> None:
        repo = FixtureRepository(db_session)
        repo.upsert([seed.fixture_item(i) for i in range(1, 6)])

        items, total = repo.list_filtered(seed.season.id, limit=2, offset=2)

        assert total == 5
        assert [f.external_id for f in items] == [3, 4]

    def test_teams_by_season(self, db_session: Session, seed: Seed) -> None:
        db_session.add(Team(external_id=549, name="Beşiktaş"))  # maçı yok
        FixtureRepository(db_session).upsert([seed.fixture_item()])

        teams = TeamRepository(db_session).list_by_season(seed.season.id)

        assert [t.name for t in teams] == ["Fenerbahçe", "Galatasaray"]

    def test_season_upsert_uses_league_and_year(self, db_session: Session, seed: Seed) -> None:
        repo = SeasonRepository(db_session)

        repo.upsert([{"league_id": seed.league.id, "year": 2024, "is_current": False}])
        repo.upsert([{"league_id": seed.league.id, "year": 2025, "is_current": True}])

        assert [s.year for s in repo.list_by_league(seed.league.id)] == [2025, 2024]


def test_latest_data_update_ignores_skipped_and_failed(db_session: Session) -> None:
    repo = SyncRunRepository(db_session)
    good = repo.try_start(SyncTrigger.MANUAL)
    repo.finish(good, SyncStatus.SUCCESS)
    bad = repo.try_start(SyncTrigger.MANUAL)
    repo.finish(bad, SyncStatus.FAILED, error_message="boom")
    repo.record_skipped(SyncTrigger.SCHEDULED, "gerek yok")

    assert repo.latest().status is SyncStatus.SKIPPED
    assert repo.latest_data_update() == good


def test_list_filtered_supports_descending_order(db_session: Session, seed: Seed) -> None:
    repo = FixtureRepository(db_session)
    repo.upsert(
        [
            seed.fixture_item(i, kickoff_at=datetime(2024, 9, i, 17, 0, tzinfo=UTC))
            for i in (1, 2, 3)
        ]
    )

    items, _ = repo.list_filtered(seed.season.id, order=SortOrder.DESC, limit=2)

    assert [f.external_id for f in items] == [3, 2]


def test_run_timestamps_are_readable_after_session_closes(db_session: Session) -> None:
    repo = SyncRunRepository(db_session)
    finished = repo.try_start(SyncTrigger.MANUAL)
    repo.finish(finished, SyncStatus.SUCCESS)
    skipped = repo.record_skipped(SyncTrigger.SCHEDULED, "gerek yok")
    db_session.expunge_all()  # zamanlanmış job sonucu oturum kapandıktan sonra okur

    assert finished.finished_at is not None and finished.started_at is not None
    assert skipped.finished_at is not None


def test_teams_by_season_can_be_limited_to_rounds(db_session: Session, seed: Seed) -> None:
    playoff_team = Team(external_id=777, name="Alt Lig Takımı")
    db_session.add(playoff_team)
    db_session.flush()
    FixtureRepository(db_session).upsert(
        [
            seed.fixture_item(1, round="Regular Season - 1"),
            seed.fixture_item(2, home_team_id=playoff_team.id, round="Relegation Round"),
        ]
    )
    repo = TeamRepository(db_session)

    assert len(repo.list_by_season(seed.season.id)) == 3
    regular = repo.list_by_season(seed.season.id, "^Regular Season")
    assert {t.name for t in regular} == {"Galatasaray", "Fenerbahçe"}


def test_latest_data_update_per_league(db_session: Session) -> None:
    repo = SyncRunRepository(db_session)
    super_lig = repo.try_start(SyncTrigger.MANUAL, 203, 2024)
    repo.finish(super_lig, SyncStatus.SUCCESS)
    premier = repo.try_start(SyncTrigger.MANUAL, 39, 2024)
    repo.finish(premier, SyncStatus.SUCCESS)

    assert repo.latest_data_update(203) == super_lig
    assert repo.latest_data_update(39) == premier
    assert repo.latest_data_update(78) is None
