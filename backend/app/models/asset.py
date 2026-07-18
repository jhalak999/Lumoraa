import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AssetType(str, enum.Enum):
    SCENE_IMAGE = "scene_image"
    VOICE_AUDIO = "voice_audio"
    SUBTITLE_FILE = "subtitle_file"
    FINAL_VIDEO = "final_video"
    THUMBNAIL = "thumbnail"


class Asset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assets"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, name="asset_type", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    public_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sequence_index: Mapped[int | None] = mapped_column(
        Integer, nullable=True, doc="Order within a set, e.g. scene image #3"
    )
    provider_used: Mapped[str | None] = mapped_column(
        String(64), nullable=True, doc="Which provider produced this asset, e.g. 'stability'"
    )
    asset_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="assets")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Asset {self.asset_type} project={self.project_id}>"
