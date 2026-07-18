import enum
import uuid

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    RESEARCHING = "researching"
    RESEARCH_READY = "research_ready"
    SCRIPTING = "scripting"
    SCRIPT_READY = "script_ready"
    PLANNING_SCENES = "planning_scenes"
    SCENES_READY = "scenes_ready"
    GENERATING_IMAGE_PROMPTS = "generating_image_prompts"
    IMAGE_PROMPTS_READY = "image_prompts_ready"
    GENERATING_IMAGES = "generating_images"
    IMAGES_READY = "images_ready"
    GENERATING_VOICE = "generating_voice"
    VOICE_READY = "voice_ready"
    GENERATING_SUBTITLES = "generating_subtitles"
    SUBTITLES_READY = "subtitles_ready"
    RENDERING_VIDEO = "rendering_video"
    VIDEO_READY = "video_ready"
    GENERATING_THUMBNAIL = "generating_thumbnail"
    GENERATING_SEO = "generating_seo"
    SEO_READY = "seo_ready"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentTone(str, enum.Enum):
    EDUCATIONAL = "educational"
    ENTERTAINING = "entertaining"
    DRAMATIC = "dramatic"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    INSPIRATIONAL = "inspirational"


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[ContentTone] = mapped_column(
        SAEnum(ContentTone, name="content_tone", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=ContentTone.EDUCATIONAL,
        nullable=False,
    )
    target_duration_seconds: Mapped[int] = mapped_column(default=60, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(
            ProjectStatus, name="project_status", values_callable=lambda enum_cls: [e.value for e in enum_cls]
        ),
        default=ProjectStatus.DRAFT,
        nullable=False,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured pipeline outputs. Kept as JSON for flexibility across agent
    # versions; each field is validated against a Pydantic schema at the
    # service boundary before being written here.
    research_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    script_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scene_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    image_prompts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    seo_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="projects")  # noqa: F821
    assets: Mapped[list["Asset"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    jobs: Mapped[list["GenerationJob"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Project {self.title} ({self.status})>"
