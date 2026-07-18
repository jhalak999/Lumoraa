import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://lumora:lumora@localhost:5432/lumora_test")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
