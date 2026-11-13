from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import joinedload

from app.core.enums import MatchStatus, SortOrder
from app.models import Fixture, FixtureChange
from app.repositories.base import BaseRepository, UpsertResult

PENDING_STATUSES = (MatchStatus.SCHEDULED, MatchStatus.LIVE, MatchStatus.POSTPONED)


class FixtureRepository(BaseRepository[Fixture]):
    model = Fixture
    TRACKED_FIELDS = ("status", "home_goals", "away_goals", "kickoff_at")

    def get_with_teams(self, fixture_id: int) -> Fixture | None:
        stmt = (
            select(Fixture)
            .options(joinedload(Fixture.home_team), joinedload(Fixture.away_team))
            .where(Fixture.id == fixture_id)
        )
        return self.session.scalar(stmt)

    def lock(self, fixture_id: int) -> Fixture | None:
        """Satırı transaction sonuna kadar kilitler ve güncel halini yeniden okur.

        Aynı maç için eşzamanlı istekler sıraya girer; ikinci istek ilkinin yazdığını görür.
        """
        stmt = (
            select(Fixture)
            .where(Fixture.id == fixture_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self.session.scalar(stmt)

    def count_statistics_fetched_since(self, since: datetime) -> int:
        stmt = select(func.count()).where(Fixture.statistics_fetched_at >= since)
        return self.session.scalar(stmt) or 0

    def list_filtered(
        self,
        season_id: int,
        *,
        status: MatchStatus | None = None,
        team_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        order: SortOrder = SortOrder.ASC,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[Fixture], int]:
        """Filtreli maç listesi + toplam kayıt sayısı (sayfalama için)."""
        filters = self._filters(season_id, status, team_id, date_from, date_to)
        ordering = (
            (Fixture.kickoff_at, Fixture.id)
            if order is SortOrder.ASC
            else (Fixture.kickoff_at.desc(), Fixture.id.desc())
        )
        stmt = (
            select(Fixture)
            .options(joinedload(Fixture.home_team), joinedload(Fixture.away_team))
            .where(*filters)
            .order_by(*ordering)
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt)), self.count(*filters)

    def list_finished(self, season_id: int, team_id: int | None = None) -> list[Fixture]:
        """Analitik hesaplamalar için skoru kesinleşmiş maçlar."""
        filters = self._filters(season_id, MatchStatus.FINISHED, team_id, None, None)
        return self.list(*filters, order_by=[Fixture.kickoff_at, Fixture.id])

    def list_recent_results(self, season_id: int, limit: int) -> list[Fixture]:
        stmt = (
            select(Fixture)
            .options(joinedload(Fixture.home_team), joinedload(Fixture.away_team))
            .where(Fixture.season_id == season_id, Fixture.status == MatchStatus.FINISHED)
            .order_by(Fixture.kickoff_at.desc(), Fixture.id.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def list_upcoming(self, season_id: int, after: datetime, limit: int) -> list[Fixture]:
        stmt = (
            select(Fixture)
            .options(joinedload(Fixture.home_team), joinedload(Fixture.away_team))
            .where(
                Fixture.season_id == season_id,
                Fixture.status == MatchStatus.SCHEDULED,
                Fixture.kickoff_at >= after,
            )
            .order_by(Fixture.kickoff_at, Fixture.id)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def count_by_season(self, season_id: int) -> int:
        return self.count(Fixture.season_id == season_id)

    def count_pending(self, season_id: int) -> int:
        """Sonucu henüz kesinleşmemiş (planlanmış, canlı, ertelenmiş) maç sayısı."""
        return self.count(Fixture.season_id == season_id, Fixture.status.in_(PENDING_STATUSES))

    def list_changes(self, fixture_id: int) -> list[FixtureChange]:
        stmt = (
            select(FixtureChange)
            .where(FixtureChange.fixture_id == fixture_id)
            .order_by(FixtureChange.changed_at, FixtureChange.id)
        )
        return list(self.session.scalars(stmt))

    def upsert_with_changes(
        self, items: Sequence[dict[str, Any]], sync_run_id: int | None = None
    ) -> UpsertResult:
        """Upsert yapar ve takip edilen alanlardaki farkları fixture_changes'a yazar."""
        items = self._dedupe(items)
        if not items:
            return UpsertResult()

        tracked_cols = [getattr(Fixture, f) for f in self.TRACKED_FIELDS]
        stmt = select(Fixture.external_id, Fixture.id, *tracked_cols).where(
            Fixture.external_id.in_({item["external_id"] for item in items})
        )
        existing = {row.external_id: row for row in self.session.execute(stmt)}

        changes: list[FixtureChange] = []
        for item in items:
            old = existing.get(item["external_id"])
            if old is None:
                continue
            for field in self.TRACKED_FIELDS:
                if field in item and getattr(old, field) != item[field]:
                    changes.append(
                        FixtureChange(
                            fixture_id=old.id,
                            sync_run_id=sync_run_id,
                            field=field,
                            old_value=_to_text(getattr(old, field)),
                            new_value=_to_text(item[field]),
                        )
                    )

        result = self.upsert(items)
        self.session.add_all(changes)
        self.session.flush()
        return result

    @staticmethod
    def _filters(
        season_id: int,
        status: MatchStatus | None,
        team_id: int | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = [Fixture.season_id == season_id]
        if status is not None:
            filters.append(Fixture.status == status)
        if team_id is not None:
            filters.append(or_(Fixture.home_team_id == team_id, Fixture.away_team_id == team_id))
        if date_from is not None:
            filters.append(Fixture.kickoff_at >= date_from)
        if date_to is not None:
            filters.append(Fixture.kickoff_at < date_to)
        return filters


def _to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
