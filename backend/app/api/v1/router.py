from fastapi import APIRouter

from app.api.v1.endpoints import assets, auth, dashboard, generation, projects

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(generation.router)
api_router.include_router(dashboard.router)
api_router.include_router(assets.router)
