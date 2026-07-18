"""
Storage abstraction.

Local disk today; swapping to S3 later means implementing `S3StorageBackend`
against the same interface and flipping `settings.STORAGE_BACKEND` — no
caller changes required (Open/Closed principle).
"""
from __future__ import annotations

import shutil
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, *, data: bytes, relative_path: str) -> str:
        """Persist bytes, return a publicly accessible URL."""
        raise NotImplementedError

    @abstractmethod
    def resolve_local_path(self, relative_path: str) -> Path:
        """Return the filesystem path for a relative path (used by FFmpeg, which needs real files)."""
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    def __init__(self) -> None:
        self.root = Path(settings.LOCAL_STORAGE_ROOT).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    async def save(self, *, data: bytes, relative_path: str) -> str:
        full_path = self.root / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)
        return f"{settings.PUBLIC_ASSET_BASE_URL.rstrip('/')}/{relative_path}"

    def resolve_local_path(self, relative_path: str) -> Path:
        return self.root / relative_path


def build_project_relative_path(project_id: uuid.UUID, subfolder: str, filename: str) -> str:
    return f"projects/{project_id}/{subfolder}/{filename}"


_backend_singleton: StorageBackend | None = None


def cleanup_old_storage_files(*, max_age_seconds: int | None = None) -> int:
    root = Path(settings.LOCAL_STORAGE_ROOT).resolve()
    if not root.exists():
        return 0

    threshold = time.time() - (max_age_seconds if max_age_seconds is not None else settings.STORAGE_MAX_AGE_SECONDS)
    removed_files = 0

    for path in root.rglob("*"):
        try:
            if path.is_file() and path.stat().st_mtime < threshold:
                path.unlink()
                removed_files += 1
        except OSError:
            continue

    for path in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(str(p)), reverse=True):
        try:
            if not any(path.iterdir()):
                path.rmdir()
        except OSError:
            continue

    return removed_files


def get_storage_backend() -> StorageBackend:
    global _backend_singleton
    if _backend_singleton is None:
        if settings.STORAGE_BACKEND == "local":
            _backend_singleton = LocalStorageBackend()
        else:
            raise NotImplementedError(
                "S3 backend not yet implemented — implement S3StorageBackend and wire it here."
            )
    return _backend_singleton
