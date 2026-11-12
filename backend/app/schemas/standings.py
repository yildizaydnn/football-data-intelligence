from app.core.enums import MatchResult
from app.schemas.common import Schema
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
    form: list[MatchResult]

    @classmethod
    def from_entry(cls, entry: StandingEntry) -> "StandingRowOut":
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
            form=row.form,
        )


class StandingsOut(Schema):
    season: int
    rows: list[StandingRowOut]

    @classmethod
    def from_standings(cls, standings: Standings) -> "StandingsOut":
        return cls(
            season=standings.season.year,
            rows=[StandingRowOut.from_entry(e) for e in standings.entries],
        )
