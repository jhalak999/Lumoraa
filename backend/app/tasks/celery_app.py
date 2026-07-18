"""
Celery application instance.

Run a worker with:
    celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4

Run the beat scheduler (not currently used for periodic tasks, but wired
for future use, e.g. nightly cleanup of orphaned storage files):
    celery -A app.tasks.celery_app beat --loglevel=info
"""
from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging as celery_setup_logging_signal

from app.core.config import settings
from app.core.logging import configure_logging

celery_app = Celery(
    "lumora",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.generation_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 20,  # hard kill after 20 min (video rendering can be slow)
    task_soft_time_limit=60 * 18,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    worker_prefetch_multiplier=1,
    result_expires=60 * 60 * 24,  # 24h
    beat_schedule={
        "cleanup-old-storage-files-daily": {
            "task": "lumora.cleanup_storage",
            "schedule": crontab(hour=3, minute=0),
            "args": (),
        }
    },
)


@celery_setup_logging_signal.connect
def _configure_worker_logging(**kwargs):  # noqa: ANN001, ARG001
    configure_logging()
