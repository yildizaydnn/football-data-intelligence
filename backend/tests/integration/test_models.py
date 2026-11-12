from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import MatchStatus
from app.models import Fixture, FixtureChange, League, Season, Team


def _create_fixture(session: Session) -> Fixture:
    league = League(external_id=203, name="Süper Lig", country="Turkey")
    season = Season(league=league, year=2024, is_current=True)
    home = Team(external_id=1, name="Galatasaray")
    away = Team(external_id=2, name="Fenerbahçe")
    fixture = Fixture(
        external_id=1001,
        season=season,
        home_team=home,
        away_team=away,
        kickoff_at=datetime(2024, 9, 21, 17, 0, tzinfo=UTC),
        status=MatchStatus.FINISHED,
        status_raw="FT",
        home_goals=1,
        away_goals=3,
    )
    session.add(fixture)
    session.flush()
    return fixture


def test_fixture_persists_with_relations(db_session: Session) -> None:
    fixture = _create_fixture(db_session)
    db_session.expire_all()

    loaded = db_session.get(Fixture, fixture.id)

    assert loaded is not None
    assert loaded.home_team.name == "Galatasaray"
    assert loaded.season.league.name == "Süper Lig"
    assert loaded.status is MatchStatus.FINISHED
    assert loaded.created_at is not None


def test_enum_is_stored_by_value(db_session: Session) -> None:
    fixture = _create_fixture(db_session)

    raw = db_session.scalar(text("SELECT status FROM fixtures WHERE id = :id"), {"id": fixture.id})

    assert raw == "finished"


def test_fixture_change_links_to_fixture(db_session: Session) -> None:
    fixture = _create_fixture(db_session)
    db_session.add(FixtureChange(fixture=fixture, field="home_goals", old_value="0", new_value="1"))
    db_session.flush()
    db_session.expire_all()

    assert [c.field for c in db_session.get(Fixture, fixture.id).changes] == ["home_goals"]


def test_external_id_is_unique(db_session: Session) -> None:
    db_session.add(Team(external_id=99, name="A"))
    db_session.flush()
    db_session.add(Team(external_id=99, name="B"))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_season_is_unique_per_league_and_year(db_session: Session) -> None:
    league = League(external_id=203, name="Süper Lig")
    db_session.add_all([Season(league=league, year=2024), Season(league=league, year=2024)])

    with pytest.raises(IntegrityError):
        db_session.flush()
