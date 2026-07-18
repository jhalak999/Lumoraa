import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.agent import ImagePromptOutput, ResearchOutput, ScenePlanOutput, ScriptOutput, SeoOutput
from app.schemas.project import (
    AssetRead,
    ProjectCreate,
    ProjectDetailRead,
    ProjectListResponse,
    ProjectRead,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, current_user: CurrentUser, db: DbSession) -> ProjectRead:
    project = await ProjectService(db).create(owner_id=current_user.id, payload=payload)
    return ProjectRead.model_validate(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
) -> ProjectListResponse:
    items, total = await ProjectService(db).list_for_owner(
        owner_id=current_user.id, page=page, page_size=page_size
    )
    return ProjectListResponse(
        items=[ProjectRead.model_validate(p) for p in items], total=total, page=page, page_size=page_size
    )


@router.get("/{project_id}", response_model=ProjectDetailRead)
async def get_project(project_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> ProjectDetailRead:
    project = await ProjectService(db).get_owned(project_id=project_id, owner_id=current_user.id)
    return ProjectDetailRead(
        **ProjectRead.model_validate(project).model_dump(),
        research_data=ResearchOutput.model_validate(project.research_data) if project.research_data else None,
        script_data=ScriptOutput.model_validate(project.script_data) if project.script_data else None,
        scene_plan=ScenePlanOutput.model_validate(project.scene_plan) if project.scene_plan else None,
        image_prompts=ImagePromptOutput.model_validate(project.image_prompts) if project.image_prompts else None,
        seo_metadata=SeoOutput.model_validate(project.seo_metadata) if project.seo_metadata else None,
        assets=[AssetRead.model_validate(a) for a in project.assets],
    )


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID, payload: ProjectUpdate, current_user: CurrentUser, db: DbSession
) -> ProjectRead:
    service = ProjectService(db)
    project = await service.get_owned(project_id=project_id, owner_id=current_user.id)
    project = await service.update(project=project, payload=payload)
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    service = ProjectService(db)
    project = await service.get_owned(project_id=project_id, owner_id=current_user.id)
    await service.delete(project=project)
