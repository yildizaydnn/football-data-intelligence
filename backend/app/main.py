from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.error_handlers import register_error_handlers
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.scheduler.setup import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler = start_scheduler(get_settings())
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


def _operation_id(route: APIRoute) -> str:
    # OpenAPI'den üretilen TS tiplerinde okunaklı isimler için (ör. get_standings).
    return route.name


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        generate_unique_id_function=_operation_id,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
