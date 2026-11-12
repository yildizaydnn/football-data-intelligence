from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.enums import MatchStatus
from app.models import Fixture, Team
from app.repositories.base import UpsertResult
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.team_repository import TeamRepository
from tests.integration.conftest import Seed


def test_same_fixture_twice_creates_single_row(db_session: Session, seed: Seed) -> None:
    repo = FixtureRepository(db_session)

    first = repo.upsert_with_changes([seed.fixture_item()])
    second = repo.upsert_with_changes([seed.fixture_item()])

    assert first == UpsertResult(inserted=1)
    assert second == UpsertResult(unchanged=1)
    assert repo.count() == 1
    fixture = repo.get_by_external_id(1001)
    assert fixture is not None
    assert repo.list_changes(fixture.id) == []


def test_changed_fixture_is_updated_and_history_recorded(db_session: Session, seed: Seed) -> None:
    repo = FixtureRepository(db_session)
    repo.upsert_with_changes([seed.fixture_item()])

    result = repo.upsert_with_changes(
        [
            seed.fixture_item(
                status=MatchStatus.FINISHED, status_raw="FT", home_goals=2, away_goals=1
            )
        ]
    )

    assert result == UpsertResult(updated=1)
    fixture = db_session.get(Fixture, repo.get_by_external_id(1001).id, populate_existing=True)
    assert (fixture.status, fixture.home_goals, fixture.away_goals) == (MatchStatus.FINISHED, 2, 1)

    changes = {c.field: (c.old_value, c.new_value) for c in repo.list_changes(fixture.id)}
    assert changes == {
        "status": ("scheduled", "finished"),
        "home_goals": (None, "2"),
        "away_goals": (None, "1"),
    }


def test_kickoff_change_is_tracked(db_session: Session, seed: Seed) -> None:
    repo = FixtureRepository(db_session)
    repo.upsert_with_changes([seed.fixture_item()])
    new_kickoff = datetime(2024, 9, 22, 19, 0, tzinfo=UTC)

    repo.upsert_with_changes([seed.fixture_item(kickoff_at=new_kickoff)])

    [change] = repo.list_changes(repo.get_by_external_id(1001).id)
    assert change.field == "kickoff_at"
    assert change.new_value == new_kickoff.isoformat()


def test_untracked_field_change_updates_without_history(db_session: Session, seed: Seed) -> None:
    repo = FixtureRepository(db_session)
    repo.upsert_with_changes([seed.fixture_item()])

    result = repo.upsert_with_changes([seed.fixture_item(round="Regular Season - 7")])

    assert result == UpsertResult(updated=1)
    assert repo.list_changes(repo.get_by_external_id(1001).id) == []


def test_duplicates_in_same_batch_are_collapsed(db_session: Session, seed: Seed) -> None:
    repo = FixtureRepository(db_session)

    result = repo.upsert_with_changes(
        [seed.fixture_item(), seed.fixture_item(home_goals=0, away_goals=0)]
    )

    assert result == UpsertResult(inserted=1)
    assert repo.get_by_external_id(1001).home_goals == 0


def test_mixed_batch_counts(db_session: Session, seed: Seed) -> None:
    repo = TeamRepository(db_session)

    result = repo.upsert(
        [
            {"external_id": 645, "name": "Galatasaray"},  # aynı → unchanged
            {"external_id": 611, "name": "Fenerbahçe SK"},  # farklı → updated
            {"external_id": 549, "name": "Beşiktaş"},  # yeni → inserted
        ]
    )

    assert result == UpsertResult(inserted=1, updated=1, unchanged=1)
    assert repo.id_map([645, 611, 549]).keys() == {645, 611, 549}
    assert db_session.get(Team, seed.away.id, populate_existing=True).name == "Fenerbahçe SK"
