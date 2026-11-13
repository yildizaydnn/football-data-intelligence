from fastapi import APIRouter

from app.api.deps import InsightServiceDep
from app.api.v1.common import error_responses
from app.schemas.insight import AiStatusOut, InsightOut, InsightRequest

router = APIRouter(tags=["insights"])


@router.get("/insights/status", response_model=AiStatusOut)
def get_ai_status(service: InsightServiceDep) -> AiStatusOut:
    """AI analizi açık mı, bugün kaç analiz üretildi."""
    return AiStatusOut.from_status(service.status())


@router.post(
    "/leagues/{league_id}/insights",
    response_model=InsightOut,
    responses=error_responses(400, 404, 429, 502, 503),
)
def create_insight(league_id: int, body: InsightRequest, service: InsightServiceDep) -> InsightOut:
    """İki takımın AI karşılaştırması. Aynı veri için önbellekten döner (LLM çağrılmaz)."""
    insight = service.compare(league_id, body.team_a_id, body.team_b_id, body.season)
    return InsightOut.from_insight(insight)
