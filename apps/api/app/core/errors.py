"""Centralized safe HTTP exception responses."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import get_logger

logger = get_logger(__name__)


class ProblemDetail(BaseModel):
    """Stable RFC 9457-style error representation."""

    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: str
    correlation_id: str
    errors: list[dict[str, Any]] | None = None


class AppError(Exception):
    """Expected application error safe to expose to clients."""

    def __init__(self, *, status_code: int, code: str, title: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.title = title
        self.detail = detail


def _correlation_id(request: Request) -> str:
    return str(getattr(request.state, "correlation_id", "unavailable"))


def _problem_response(problem: ProblemDetail) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
    """Translate known domain/application errors."""
    return _problem_response(
        ProblemDetail(
            type=f"https://api.msme-saarthi.example/problems/{error.code}",
            title=error.title,
            status=error.status_code,
            detail=error.detail,
            instance=request.url.path,
            code=error.code,
            correlation_id=_correlation_id(request),
        )
    )


async def validation_error_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    """Translate Pydantic validation failures without exposing input values."""
    errors = [
        {
            "field": ".".join(str(part) for part in item["loc"]),
            "code": item["type"],
            "message": item["msg"],
        }
        for item in error.errors()
    ]
    return _problem_response(
        ProblemDetail(
            type="https://api.msme-saarthi.example/problems/validation-error",
            title="Request validation failed",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more fields are invalid.",
            instance=request.url.path,
            code="validation_error",
            correlation_id=_correlation_id(request),
            errors=errors,
        )
    )


async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
    """Hide unexpected implementation details and log with a correlation identifier."""
    correlation_id = _correlation_id(request)
    logger.exception("unhandled_exception", extra={"correlation_id": correlation_id})
    return _problem_response(
        ProblemDetail(
            type="https://api.msme-saarthi.example/problems/internal-error",
            title="Internal server error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
            instance=request.url.path,
            code="internal_error",
            correlation_id=correlation_id,
        )
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all application exception handlers in one place."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unexpected_error_handler)

