from fastapi import APIRouter

from app.api.v1 import fixtures, leagues, overview, standings, sync, teams

api_router = APIRouter(prefix="/api/v1")
for module in (leagues, teams, fixtures, standings, overview, sync):
    api_router.include_router(module.router)
