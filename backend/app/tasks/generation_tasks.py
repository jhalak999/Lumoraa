"""
Celery tasks — the async/sync bridge.

Celery tasks themselves are synchronous by nature; our services are async
(SQLAlchemy async session, httpx async clients). Each task wraps its async
body in `asyncio.run(...)`. Every task also creates/updates a
`GenerationJob` row so the frontend can poll granular progress instead of
only seeing the coarse `project.status`.
"""
from __future__ import annotations

import asyncio
import uuid

from celery import chain
from celery.utils.log import get_task_logger

from app.core.exceptions import LumoraError
from app.db.session import session_scope
from app.models.job import GenerationJob, JobStage, JobStatus
from app.models.project import Project, ProjectStatus
from app.services.generation_service import GenerationService
from app.services.storage_service import cleanup_old_storage_files
from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


async def _update_job(job_id: uuid.UUID, **fields) -> None:
    async with session_scope() as db:
        job = await db.get(GenerationJob, job_id)
        if job:
            for key, value in fields.items():
                setattr(job, key, value)


async def _create_job(project_id: uuid.UUID, stage: JobStage, celery_task_id: str) -> uuid.UUID:
    async with session_scope() as db:
        job = GenerationJob(
            project_id=project_id, stage=stage, celery_task_id=celery_task_id, status=JobStatus.PENDING
        )
        db.add(job)
        await db.flush()
        return job.id


async def _run_stage(project_id_str: str, stage: JobStage, task_id: str, method_name: str) -> str:
    project_id = uuid.UUID(project_id_str)
    job_id = await _create_job(project_id, stage, task_id)
    await _update_job(job_id, status=JobStatus.RUNNING, progress_percent=10)

    try:
        async with session_scope() as db:
            service = GenerationService(db)
            method = getattr(service, method_name)
            result = await method(project_id)
        await _update_job(job_id, status=JobStatus.SUCCEEDED, progress_percent=100)
        return str(result)
    except LumoraError as exc:
        logger.error("Stage %s failed for project=%s: %s", stage, project_id, exc.message)
        await _update_job(job_id, status=JobStatus.FAILED, error_message=exc.message)
        async with session_scope() as db:
            project = await db.get(Project, project_id)
            if project:
                project.status = ProjectStatus.FAILED
                project.error_message = exc.message
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected failure in stage %s for project=%s", stage, project_id)
        await _update_job(job_id, status=JobStatus.FAILED, error_message=str(exc))
        raise


def _sync(coro):
    return asyncio.run(coro)


@celery_app.task(bind=True, name="lumora.generate_research", max_retries=1)
def generate_research_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.RESEARCH, self.request.id, "generate_research"))


@celery_app.task(bind=True, name="lumora.generate_script", max_retries=1)
def generate_script_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.SCRIPT, self.request.id, "generate_script"))


@celery_app.task(bind=True, name="lumora.generate_scene_plan", max_retries=1)
def generate_scene_plan_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.SCENE_PLAN, self.request.id, "generate_scene_plan"))


@celery_app.task(bind=True, name="lumora.generate_image_prompts", max_retries=1)
def generate_image_prompts_task(self, project_id: str) -> str:
    return _sync(
        _run_stage(project_id, JobStage.IMAGE_PROMPTS, self.request.id, "generate_image_prompts")
    )


@celery_app.task(bind=True, name="lumora.generate_images", max_retries=2)
def generate_images_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.IMAGES, self.request.id, "generate_images"))


@celery_app.task(bind=True, name="lumora.generate_voice", max_retries=2)
def generate_voice_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.VOICE, self.request.id, "generate_voice"))


@celery_app.task(bind=True, name="lumora.generate_subtitles", max_retries=1)
def generate_subtitles_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.SUBTITLES, self.request.id, "generate_subtitles"))


@celery_app.task(bind=True, name="lumora.render_video", max_retries=1)
def render_video_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.VIDEO, self.request.id, "render_video"))


@celery_app.task(bind=True, name="lumora.generate_thumbnail", max_retries=1)
def generate_thumbnail_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.THUMBNAIL, self.request.id, "generate_thumbnail"))


@celery_app.task(bind=True, name="lumora.generate_seo", max_retries=1)
def generate_seo_task(self, project_id: str) -> str:
    return _sync(_run_stage(project_id, JobStage.SEO, self.request.id, "generate_seo"))


@celery_app.task(name="lumora.run_full_pipeline")
def run_full_pipeline_task(project_id: str) -> None:
    """
    Enqueues every stage as a Celery `chain` so they execute strictly in
    order on the worker pool, with each stage only starting once the prior
    one has committed its DB state. If any stage raises, Celery halts the
    chain (task_always_eager aside) and the project is left in FAILED with
    error_message populated for the frontend to surface.
    """
    # Use immutable signatures (`.si`) — each stage only needs `project_id`,
    # not the previous task's return value, so we explicitly ignore it
    # rather than let Celery append it as an extra positional arg.
    pipeline = chain(
        generate_research_task.si(project_id),
        generate_script_task.si(project_id),
        generate_scene_plan_task.si(project_id),
        generate_image_prompts_task.si(project_id),
        generate_seo_task.si(project_id),
        generate_images_task.si(project_id),
        generate_voice_task.si(project_id),
        generate_subtitles_task.si(project_id),
        render_video_task.si(project_id),
        generate_thumbnail_task.si(project_id),
    )
    pipeline.apply_async()


@celery_app.task(name="lumora.cleanup_storage")
def cleanup_storage_task() -> int:
    """Removes local storage files older than STORAGE_MAX_AGE_SECONDS."""
    return cleanup_old_storage_files()
