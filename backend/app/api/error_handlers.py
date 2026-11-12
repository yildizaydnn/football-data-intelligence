"""Tüm hatalar aynı biçimde döner: {"error": {"code", "message", "details"?}}."""

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.exceptions import AppError
from app.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def _error(status_code: int, code: str, message: str, details: list | None = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body, exclude_none=True))


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error(exc.status_code, exc.code, exc.message)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(map(str, err["loc"])), "message": err["msg"]} for err in exc.errors()
    ]
    return _error(422, "validation_error", "İstek parametreleri geçersiz", details)


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == 404 else "http_error"
    return _error(exc.status_code, code, str(exc.detail))


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Beklenmeyen hata: %s %s", request.method, request.url.path)
    return _error(500, "internal_error", "Beklenmeyen bir hata oluştu")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
