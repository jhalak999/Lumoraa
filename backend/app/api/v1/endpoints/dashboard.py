from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.job import DashboardStats
from app.services.project_service import ProjectService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: CurrentUser, db: DbSession) -> DashboardStats:
    return await ProjectService(db).get_stats(owner_id=current_user.id)
