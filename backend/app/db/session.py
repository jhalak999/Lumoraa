"""
Async SQLAlchemy engine + session factory.

We use the async engine (asyncpg driver) for the FastAPI app, and expose a
`get_db` dependency that yields a session per-request and always closes it,
committing on success and rolling back on error.

TWO ENGINES ON PURPOSE — this is not an accident or duplication:

- `engine` / `AsyncSessionLocal` (used by `get_db`, the FastAPI dependency):
  a normally-pooled engine. FastAPI/uvicorn runs ONE persistent event loop
  for the life of the process, so pooling and reusing asyncpg connections
  across requests within that single loop is safe and efficient.

- `celery_engine` / `CelerySessionLocal` (used by `session_scope`, for
  Celery tasks and standalone scripts): a NullPool engine — every checkout
  opens a brand-new DBAPI connection and closes it on return, with nothing
  reused across calls. This is required, not just a performance choice:
  each Celery task in this codebase runs its async body via a fresh
  `asyncio.run(...)` call (see app/tasks/generation_tasks.py `_sync()`),
  which creates a NEW event loop every single time. asyncpg connections are
  bound to the event loop they were created under, so a normal connection
  pool WILL eventually hand a task a connection that was opened under a
  previous task's (now-closed) event loop, raising
  "got Future ... attached to a different loop". Using NullPool for this
  code path sidesteps the issue entirely by never carrying a connection
  across an asyncio.run() boundary. If you ever change generation_tasks.py
  to reuse a single long-lived event loop across tasks (e.g. via a custom
  Celery worker process pool), `celery_engine` could go back to normal
  pooling — but as long as `_sync()` uses `asyncio.run()` per task, this
  must stay NullPool.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Normalize the URL to the async driver regardless of what's configured.
_async_url = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://").replace(
    "postgresql://", "postgresql+asyncpg://"
)

# --- FastAPI request-scoped engine (pooled) ---
engine = create_async_engine(
    _async_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)

# --- Celery / script-scoped engine (NullPool — see module docstring) ---
celery_engine = create_async_engine(
    _async_url,
    poolclass=NullPool,
    echo=settings.DEBUG,
)

CelerySessionLocal = async_sessionmaker(
    bind=celery_engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a request-scoped DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for use OUTSIDE of request scope (Celery tasks, scripts).

    Uses the NullPool `celery_engine` — see module docstring for why this
    must not share a connection pool with the FastAPI-side engine.
    """
    async with CelerySessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
