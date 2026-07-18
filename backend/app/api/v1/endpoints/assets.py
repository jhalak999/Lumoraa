import uuid

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.asset import Asset
from app.services.project_service import ProjectService
from app.services.storage_service import get_storage_backend

router = APIRouter(prefix="/assets", tags=["assets"])

_EXTENSION_BY_TYPE = {
    "scene_image": "png",
    "voice_audio": "mp3",
    "subtitle_file": "srt",
    "final_video": "mp4",
    "thumbnail": "jpg",
}


@router.get("/{asset_id}/download")
async def download_asset(asset_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> FileResponse:
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise NotFoundError("Asset not found.")

    # Ownership check via the parent project — an asset has no owner of its own.
    await ProjectService(db).get_owned(project_id=asset.project_id, owner_id=current_user.id)

    storage = get_storage_backend()
    local_path = storage.resolve_local_path(asset.storage_path)
    if not local_path.exists():
        raise NotFoundError("Asset file is missing from storage.")

    extension = _EXTENSION_BY_TYPE.get(asset.asset_type.value, "bin")
    download_name = f"lumora_{asset.asset_type.value}_{asset.sequence_index or ''}.{extension}".replace(
        "__", "_"
    )
    return FileResponse(path=local_path, filename=download_name, media_type="application/octet-stream")
