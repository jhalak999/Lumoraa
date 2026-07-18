from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.logging import get_logger
from app.models.asset import Asset, AssetType
from app.models.job import GenerationJob
from app.models.project import Project, ProjectStatus
from app.schemas.job import DashboardStats
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = get_logger(__name__)

_FAILED_OR_TERMINAL = {ProjectStatus.FAILED}
_COMPLETED = {ProjectStatus.COMPLETED}


class ProjectService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, *, owner_id: uuid.UUID, payload: ProjectCreate) -> Project:
        project = Project(
            owner_id=owner_id,
            title=payload.title,
            topic=payload.topic,
            tone=payload.tone,
            target_duration_seconds=payload.target_duration_seconds,
            status=ProjectStatus.DRAFT,
        )
        self.db.add(project)
        await self.db.flush()
        logger.info("Project created id=%s owner=%s", project.id, owner_id)
        return project

    async def get_owned(self, *, project_id: uuid.UUID, owner_id: uuid.UUID) -> Project:
        project = await self.db.get(Project, project_id)
        if not project:
            raise NotFoundError("Project not found.")
        if project.owner_id != owner_id:
            raise PermissionDeniedError("You do not have access to this project.")
        return project

    async def list_for_owner(
        self, *, owner_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[Project], int]:
        base_query = select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at.desc())
        total = await self.db.scalar(
            select(func.count()).select_from(base_query.subquery())
        )
        result = await self.db.execute(base_query.offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total or 0

    async def update(self, *, project: Project, payload: ProjectUpdate) -> Project:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self.db.flush()
        return project

    async def delete(self, *, project: Project) -> None:
        await self.db.delete(project)
        await self.db.flush()

    async def add_asset(
        self,
        *,
        project_id: uuid.UUID,
        asset_type: AssetType,
        storage_path: str,
        public_url: str,
        sequence_index: int | None = None,
        provider_used: str | None = None,
        file_size_bytes: int | None = None,
        metadata: dict | None = None,
    ) -> Asset:
        asset = Asset(
            project_id=project_id,
            asset_type=asset_type,
            storage_path=storage_path,
            public_url=public_url,
            sequence_index=sequence_index,
            provider_used=provider_used,
            file_size_bytes=file_size_bytes,
            asset_metadata=metadata,
        )
        self.db.add(asset)
        await self.db.flush()
        return asset

    async def get_stats(self, *, owner_id: uuid.UUID) -> DashboardStats:
        projects_result = await self.db.execute(
            select(Project).where(Project.owner_id == owner_id)
        )
        projects = list(projects_result.scalars().all())

        status_counts: dict[str, int] = {}
        for p in projects:
            status_counts[p.status.value] = status_counts.get(p.status.value, 0) + 1

        completed = sum(1 for p in projects if p.status in _COMPLETED)
        failed = sum(1 for p in projects if p.status in _FAILED_OR_TERMINAL)
        in_progress = len(projects) - completed - failed

        video_count = await self.db.scalar(
            select(func.count())
            .select_from(Asset)
            .join(Project, Asset.project_id == Project.id)
            .where(Project.owner_id == owner_id, Asset.asset_type == AssetType.FINAL_VIDEO)
        )

        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_projects_render_seconds = sum(
            p.target_duration_seconds
            for p in projects
            if p.status in _COMPLETED and p.updated_at >= month_start
        )

        recent = sorted(projects, key=lambda p: p.created_at, reverse=True)[:5]
        recent_payload = [
            {
                "id": str(p.id),
                "title": p.title,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
            }
            for p in recent
        ]

        return DashboardStats(
            total_projects=len(projects),
            completed_projects=completed,
            in_progress_projects=max(in_progress, 0),
            failed_projects=failed,
            total_videos_generated=video_count or 0,
            total_render_seconds_this_month=float(month_projects_render_seconds),
            projects_by_status=status_counts,
            recent_projects=recent_payload,
        )
