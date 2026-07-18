import uuid

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.job import GenerationJob
from app.schemas.job import JobRead
from app.services.project_service import ProjectService
from app.tasks import generation_tasks

router = APIRouter(prefix="/projects/{project_id}/generate", tags=["generation"])

# Maps a URL segment to the Celery task that should be enqueued for it.
_STAGE_TASKS = {
    "research": generation_tasks.generate_research_task,
    "script": generation_tasks.generate_script_task,
    "scenes": generation_tasks.generate_scene_plan_task,
    "image-prompts": generation_tasks.generate_image_prompts_task,
    "images": generation_tasks.generate_images_task,
    "voice": generation_tasks.generate_voice_task,
    "subtitles": generation_tasks.generate_subtitles_task,
    "video": generation_tasks.render_video_task,
    "thumbnail": generation_tasks.generate_thumbnail_task,
    "seo": generation_tasks.generate_seo_task,
}


async def _ensure_ownership(project_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    # Raises NotFoundError/PermissionDeniedError if the caller doesn't own the project.
    await ProjectService(db).get_owned(project_id=project_id, owner_id=current_user.id)


@router.post("/full-pipeline", status_code=status.HTTP_202_ACCEPTED)
async def trigger_full_pipeline(project_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    await _ensure_ownership(project_id, current_user, db)
    generation_tasks.run_full_pipeline_task.delay(str(project_id))
    return {"message": "Full generation pipeline started.", "project_id": str(project_id)}


@router.post("/{stage}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_stage(
    project_id: uuid.UUID, stage: str, current_user: CurrentUser, db: DbSession
) -> dict:
    from app.core.exceptions import ValidationError

    await _ensure_ownership(project_id, current_user, db)
    task = _STAGE_TASKS.get(stage)
    if not task:
        raise ValidationError(
            f"Unknown generation stage '{stage}'.", details={"valid_stages": list(_STAGE_TASKS)}
        )
    task.delay(str(project_id))
    return {"message": f"Stage '{stage}' started.", "project_id": str(project_id)}


@router.get("/jobs", response_model=list[JobRead])
async def list_jobs(project_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> list[JobRead]:
    await _ensure_ownership(project_id, current_user, db)
    result = await db.execute(
        select(GenerationJob)
        .where(GenerationJob.project_id == project_id)
        .order_by(GenerationJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return [JobRead.model_validate(j) for j in jobs]
