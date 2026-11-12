from app.rules.models import RuleContext, Zone, ZoneKind
from app.schemas.common import Schema


class PointsOut(Schema):
    win: int
    draw: int
    loss: int


class ZoneOut(Schema):
    from_position: int  # pozitif: üstten, negatif: alttan (-1 = son)
    to_position: int
    kind: ZoneKind
    label: str

    @classmethod
    def from_zone(cls, zone: Zone) -> "ZoneOut":
        return cls(
            from_position=zone.from_position,
            to_position=zone.to_position,
            kind=zone.kind,
            label=zone.label,
        )


class RulesOut(Schema):
    """Bir lig + sezon için geçerli kurallar (rules spec katmanından)."""

    league_external_id: int | None
    season: int | None
    name: str
    verified: bool
    sources: list[str]
    notes: str | None
    points: PointsOut
    tiebreakers: list[str]
    head_to_head_requires_all_matches: bool
    include_rounds: str | None
    zones: list[ZoneOut]

    @classmethod
    def from_context(cls, ctx: RuleContext) -> "RulesOut":
        s = ctx.standings
        return cls(
            league_external_id=ctx.league_external_id,
            season=ctx.season,
            name=ctx.meta.name,
            verified=ctx.meta.verified,
            sources=ctx.meta.sources,
            notes=ctx.meta.notes,
            points=PointsOut(win=s.points.win, draw=s.points.draw, loss=s.points.loss),
            tiebreakers=s.tiebreakers,
            head_to_head_requires_all_matches=s.head_to_head.requires_all_matches,
            include_rounds=s.include_rounds,
            zones=[ZoneOut.from_zone(z) for z in ctx.zones],
        )
