import enum
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class JobStage(str, enum.Enum):
    RESEARCH = "research"
    SCRIPT = "script"
    SCENE_PLAN = "scene_plan"
    IMAGE_PROMPTS = "image_prompts"
    IMAGES = "images"
    VOICE = "voice"
    SUBTITLES = "subtitles"
    VIDEO = "video"
    THUMBNAIL = "thumbnail"
    SEO = "seo"
    FULL_PIPELINE = "full_pipeline"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class GenerationJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tracks a single Celery task's lifecycle so the frontend can poll for
    progress (`GET /projects/{id}/jobs`) instead of relying purely on
    project.status, which only reflects the *last completed* stage.
    """

    __tablename__ = "generation_jobs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    stage: Mapped[JobStage] = mapped_column(
        SAEnum(JobStage, name="job_stage", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=JobStatus.PENDING,
        nullable=False,
    )
    progress_percent: Mapped[int] = mapped_column(default=0, nullable=False)
    progress_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="jobs")  # noqa: F821
