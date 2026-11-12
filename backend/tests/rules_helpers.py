"""Testler için kural yardımcıları: gerçek spec dosyalarından çözülür (sabit kural yazılmaz)."""

from app.analytics.standings import StandingsRules
from app.rules.engine import get_rule_engine

SUPER_LIG = 203


def status_map(league: int | None = SUPER_LIG):
    return get_rule_engine().resolve(league).cleaning.status_map


def points_table(league: int | None = SUPER_LIG):
    return get_rule_engine().resolve(league).points_table


def standings_rules(league: int | None = SUPER_LIG, season: int | None = None, **overrides):
    """Spec'ten gelen kurallar; testte gerekirse alanlar değiştirilir (ör. round_pattern=None)."""
    rules = get_rule_engine().resolve(league, season).standings_rules({})
    return StandingsRules(**{**rules.__dict__, **overrides}) if overrides else rules
