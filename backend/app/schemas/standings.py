from app.core.enums import MatchResult
from app.schemas.common import Schema
from app.schemas.rules import RulesOut, ZoneOut
from app.schemas.team import TeamRef
from app.services.standings_service import StandingEntry, Standings


class StandingRowOut(Schema):
    position: int
    team: TeamRef
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    deduction: int  # puan silme cezası (spec'ten)
    form: list[MatchResult]
    zone: ZoneOut | None = None

    @classmethod
    def from_entry(cls, entry: StandingEntry, zone: ZoneOut | None = None) -> "StandingRowOut":
        row = entry.row
        return cls(
            position=row.position,
            team=TeamRef.model_validate(entry.team),
            played=row.played,
            won=row.won,
            drawn=row.drawn,
            lost=row.lost,
            goals_for=row.goals_for,
            goals_against=row.goals_against,
            goal_difference=row.goal_difference,
            points=row.points,
            deduction=row.deduction,
            form=row.form,
            zone=zone,
        )


class StandingsOut(Schema):
    season: int
    rows: list[StandingRowOut]
    rules: RulesOut

    @classmethod
    def from_standings(cls, standings: Standings) -> "StandingsOut":
        total = len(standings.entries)

        def zone(position: int) -> ZoneOut | None:
            found = standings.rules.zone_for(position, total)
            return ZoneOut.from_zone(found) if found else None

        return cls(
            season=standings.season.year,
            rows=[StandingRowOut.from_entry(e, zone(e.row.position)) for e in standings.entries],
            rules=RulesOut.from_context(standings.rules),
        )
