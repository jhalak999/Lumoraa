"""
Application exception hierarchy + FastAPI exception handlers.

Design principle: services and agents raise domain-specific exceptions
(never raw HTTPException). The API layer is the ONLY place that knows about
HTTP status codes. This keeps services usable outside of HTTP (e.g. from
Celery tasks, CLI scripts, tests) without dragging FastAPI along.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class LumoraError(Exception):
    """Base class for all application-raised errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, details: dict | None = None):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(LumoraError):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Resource not found."


class AlreadyExistsError(LumoraError):
    status_code = status.HTTP_409_CONFLICT
    default_message = "Resource already exists."


class InvalidCredentialsError(LumoraError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Invalid credentials."


class NotAuthenticatedError(LumoraError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Authentication required."


class PermissionDeniedError(LumoraError):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "You do not have permission to perform this action."


class ValidationError(LumoraError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_message = "Invalid input."


class ProjectStateError(LumoraError):
    """Raised when an action is attempted on a project in the wrong pipeline stage."""

    status_code = status.HTTP_409_CONFLICT
    default_message = "Project is not in a valid state for this action."


class AgentExecutionError(LumoraError):
    """Raised when an AI agent fails to produce a usable result after retries."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_message = "AI generation step failed."


class AllProvidersFailedError(AgentExecutionError):
    """Raised when every provider in a fallback chain has failed."""

    default_message = "All configured providers failed for this operation."


class MediaProcessingError(LumoraError):
    """Raised for FFmpeg / audio / video / subtitle processing failures."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "Media processing failed."


class RateLimitExceededError(LumoraError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_message = "Rate limit exceeded. Please try again shortly."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LumoraError)
    async def handle_lumora_error(request: Request, exc: LumoraError) -> JSONResponse:
        logger.warning(
            "Handled application error: %s | path=%s | details=%s",
            exc.message,
            request.url.path,
            exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on path=%s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Our team has been notified.",
                "details": {},
            },
        )
