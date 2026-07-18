from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger, request_id_ctx

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="AI Content Automation Studio — turn a topic into a fully produced short-form video.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attaches a request id to every log line emitted while handling this request,
    and records basic timing for observability."""
    request_id = str(uuid.uuid4())
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.1f}"
    return response


register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Serve generated media (images/audio/video/subtitles/thumbnails) directly.
# In production this would typically be offloaded to S3 + CloudFront/CDN;
# local static serving is fine for self-hosted or small-scale deployments.
app.mount("/static", StaticFiles(directory=settings.LOCAL_STORAGE_ROOT), name="static")


@app.get("/api/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT}
