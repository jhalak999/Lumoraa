import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.project import ContentTone, ProjectStatus
from app.schemas.agent import ImagePromptOutput, ResearchOutput, ScenePlanOutput, ScriptOutput, SeoOutput


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    topic: str = Field(min_length=1, max_length=5000)
    tone: ContentTone = ContentTone.EDUCATIONAL
    target_duration_seconds: int = Field(default=60, ge=15, le=600)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    topic: str | None = Field(default=None, min_length=1, max_length=5000)
    tone: ContentTone | None = None
    target_duration_seconds: int | None = Field(default=None, ge=15, le=600)


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_type: str
    public_url: str
    sequence_index: int | None
    provider_used: str | None
    created_at: datetime


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    topic: str
    tone: ContentTone
    target_duration_seconds: int
    status: ProjectStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ProjectDetailRead(ProjectRead):
    research_data: ResearchOutput | None = None
    script_data: ScriptOutput | None = None
    scene_plan: ScenePlanOutput | None = None
    image_prompts: ImagePromptOutput | None = None
    seo_metadata: SeoOutput | None = None
    assets: list[AssetRead] = []


class ProjectListResponse(BaseModel):
    items: list[ProjectRead]
    total: int
    page: int
    page_size: int
