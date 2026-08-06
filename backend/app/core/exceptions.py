"""Domain exceptions and the FastAPI handlers that turn every error path —
a raised `AppError`, a plain `HTTPException`, a Pydantic validation
failure, or a genuinely unhandled bug — into the same JSON error envelope:

    {"error": {"code": "not_found", "message": "..."}}

Existing `raise HTTPException(status, "...")` call sites across the
modules keep working unchanged; the handler below normalizes them into
this envelope too, so no call site had to move. `AppError` and its
subclasses exist for new code that wants a status code implied by the
exception type rather than passed as a magic number at every call site.
"""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for expected application errors that should reach the
    client as structured JSON rather than an unhandled-exception 500."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ServiceUnavailableError(AppError):
    """Raised when a feature's dependencies aren't usable on this host —
    see each module's `check_available()` — as opposed to a bug."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "service_unavailable"


def _envelope(status_code: int, code: str, message: str, details: object = None) -> JSONResponse:
    body: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content={"error": body})


def register_exception_handlers(app: FastAPI) -> None:
    """Wire up the handlers above. Call once during app construction."""

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return _envelope(exc.status_code, exc.code, exc.message)

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        return _envelope(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _envelope(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "Request validation failed.",
            details=exc.errors(),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        message = "Internal server error." if settings.environment == "production" else str(exc)
        return _envelope(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", message)
