"""AI karşılaştırma (Bonus C): iki takımın veritabanındaki maçlarından üretilen kısa analiz.

Sayılar analytics'ten gelir, LLM yalnızca yorumlar. Sonuç saklanır: aynı veri için LLM'e tekrar
gidilmez; veri değişince (yeni maç) otomatik yeniden üretilir. Metindeki sayılar veriyle
karşılaştırılır, veride olmayanlar `unverified_numbers` olarak işaretlenir.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, time

from sqlalchemy.orm import Session

from app.analytics.common import in_rounds
from app.analytics.comparison import TeamComparison, compare_teams
from app.core.config import Settings
from app.core.exceptions import AiNotConfiguredError, BadRequestError, QuotaExceededError
from app.insights.grounding import unverified_numbers
from app.insights.prompt import SYSTEM_PROMPT, build_facts, build_prompt, facts_hash, season_label
from app.models import Season, Team, TeamInsight
from app.providers.llm.base import TextGenerator
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.insight_repository import InsightRepository
from app.repositories.team_repository import TeamRepository
from app.rules.engine import RuleEngine
from app.services.league_service import LeagueService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Insight:
    season: Season
    team_a: Team
    team_b: Team
    comparison: TeamComparison
    content: str
    model: str
    generated_at: datetime
    cached: bool
    unverified_numbers: list[str]


@dataclass(frozen=True)
class AiStatus:
    enabled: bool
    daily_limit: int
    generated_today: int


class InsightService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        leagues: LeagueService,
        rules: RuleEngine,
        generator: TextGenerator | None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.leagues = leagues
        self.rules = rules
        self.generator = generator
        self.fixtures = FixtureRepository(session)
        self.teams = TeamRepository(session)
        self.insights = InsightRepository(session)

    def status(self) -> AiStatus:
        return AiStatus(
            enabled=self.generator is not None,
            daily_limit=self.settings.ai_daily_limit,
            generated_today=self.insights.count_generated_since(_utc_midnight()),
        )

    def compare(
        self, league_id: int, team_x_id: int, team_y_id: int, season_year: int | None = None
    ) -> Insight:
        if team_x_id == team_y_id:
            raise BadRequestError("Karşılaştırma için iki farklı takım seçin")
        league = self.leagues.get_league(league_id)
        season = self.leagues.resolve_season(league_id, season_year)
        context = self.rules.resolve(league.external_id, season.year)
        rounds = context.standings.include_rounds
        in_season = {t.id: t for t in self.teams.list_by_season(season.id, rounds)}
        if team_x_id not in in_season or team_y_id not in in_season:
            raise BadRequestError("Takımlardan biri bu sezonda ligde yer almıyor")

        # Çift sıralı: (A, B) ile (B, A) aynı analizdir.
        team_a, team_b = sorted((in_season[team_x_id], in_season[team_y_id]), key=lambda t: t.id)
        # Takım analizi ve puan tablosuyla aynı maçlar (kural dışı turlar sayılmaz).
        matches = in_rounds(self.fixtures.list_finished(season.id), rounds)
        comparison = compare_teams(team_a.id, team_b.id, matches, context.points_table)
        facts = build_facts(
            comparison,
            league=league.name,
            season=season_label(season.year),
            team_a=team_a.name,
            team_b=team_b.name,
            team_names={t.id: t.name for t in in_season.values()},
        )
        digest = facts_hash(facts)

        stored = self.insights.get_for_pair(season.id, team_a.id, team_b.id)
        if stored is not None and stored.facts_hash == digest:
            return self._result(season, team_a, team_b, comparison, stored, cached=True)

        stored = self._generate(season, team_a, team_b, facts, digest, stored)
        return self._result(season, team_a, team_b, comparison, stored, cached=False)

    def _generate(
        self,
        season: Season,
        team_a: Team,
        team_b: Team,
        facts: dict,
        digest: str,
        stored: TeamInsight | None,
    ) -> TeamInsight:
        if self.generator is None:
            raise AiNotConfiguredError(
                "AI analizi yapılandırılmamış (GEMINI_API_KEY / OPENROUTER_API_KEY tanımlı değil)"
            )
        if self.insights.count_generated_since(_utc_midnight()) >= self.settings.ai_daily_limit:
            raise QuotaExceededError("Günlük AI analiz sınırı doldu; yarın tekrar deneyin")

        generated = self.generator.generate(system=SYSTEM_PROMPT, prompt=build_prompt(facts))
        unverified = unverified_numbers(generated.text, facts)
        if unverified:
            logger.warning("AI metninde veriyle doğrulanamayan sayılar: %s", unverified)

        insight = stored or TeamInsight(
            season_id=season.id, team_a_id=team_a.id, team_b_id=team_b.id
        )
        insight.facts_hash = digest
        insight.facts = facts
        insight.content = generated.text
        insight.model = generated.model
        insight.unverified_numbers = unverified
        insight.generated_at = datetime.now(UTC)
        self.session.add(insight)
        self.session.commit()
        return insight

    @staticmethod
    def _result(
        season: Season,
        team_a: Team,
        team_b: Team,
        comparison: TeamComparison,
        stored: TeamInsight,
        *,
        cached: bool,
    ) -> Insight:
        return Insight(
            season=season,
            team_a=team_a,
            team_b=team_b,
            comparison=comparison,
            content=stored.content,
            model=stored.model,
            generated_at=stored.generated_at,
            cached=cached,
            unverified_numbers=list(stored.unverified_numbers or []),
        )


def _utc_midnight() -> datetime:
    return datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
