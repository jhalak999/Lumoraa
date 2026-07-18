import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStage, JobStatus


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    stage: JobStage
    status: JobStatus
    progress_percent: int
    progress_message: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DashboardStats(BaseModel):
    total_projects: int
    completed_projects: int
    in_progress_projects: int
    failed_projects: int
    total_videos_generated: int
    total_render_seconds_this_month: float
    projects_by_status: dict[str, int]
    recent_projects: list[dict]
