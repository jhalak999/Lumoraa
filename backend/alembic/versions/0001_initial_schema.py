"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # NOTE on create_type=False: each enum below is created explicitly via
    # `.create(bind, checkfirst=True)` BEFORE the table that uses it. Without
    # create_type=False, SQLAlchemy's ENUM type (create_type=True by default)
    # would ALSO try to create the same type a second time as part of the
    # CREATE TABLE DDL that follows — with no checkfirst protection on that
    # second attempt — causing "type already exists" even on a fresh DB.
    # create_type=False tells create_table "don't touch type creation, I've
    # already handled it," so the type is created exactly once.
    content_tone_enum = postgresql.ENUM(
        "educational", "entertaining", "dramatic", "professional", "casual", "inspirational",
        name="content_tone",
        create_type=False,
    )
    project_status_enum = postgresql.ENUM(
        "draft", "researching", "research_ready", "scripting", "script_ready",
        "planning_scenes", "scenes_ready", "generating_image_prompts", "image_prompts_ready",
        "generating_images", "images_ready", "generating_voice", "voice_ready",
        "generating_subtitles", "subtitles_ready", "rendering_video", "video_ready",
        "generating_thumbnail", "generating_seo", "completed", "failed",
        name="project_status",
        create_type=False,
    )
    content_tone_enum.create(op.get_bind(), checkfirst=True)
    project_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("tone", content_tone_enum, nullable=False, server_default="educational"),
        sa.Column("target_duration_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("status", project_status_enum, nullable=False, server_default="draft"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("research_data", sa.JSON(), nullable=True),
        sa.Column("script_data", sa.JSON(), nullable=True),
        sa.Column("scene_plan", sa.JSON(), nullable=True),
        sa.Column("image_prompts", sa.JSON(), nullable=True),
        sa.Column("seo_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    asset_type_enum = postgresql.ENUM(
        "scene_image", "voice_audio", "subtitle_file", "final_video", "thumbnail",
        name="asset_type",
        create_type=False,
    )
    asset_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_type", asset_type_enum, nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("public_url", sa.String(1024), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("sequence_index", sa.Integer(), nullable=True),
        sa.Column("provider_used", sa.String(64), nullable=True),
        sa.Column("asset_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_assets_project_id", "assets", ["project_id"])

    job_stage_enum = postgresql.ENUM(
        "research", "script", "scene_plan", "image_prompts", "images", "voice",
        "subtitles", "video", "thumbnail", "seo", "full_pipeline",
        name="job_stage",
        create_type=False,
    )
    job_status_enum = postgresql.ENUM(
        "pending", "running", "succeeded", "failed",
        name="job_status",
        create_type=False,
    )
    job_stage_enum.create(op.get_bind(), checkfirst=True)
    job_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=False),
        sa.Column("stage", job_stage_enum, nullable=False),
        sa.Column("status", job_status_enum, nullable=False, server_default="pending"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_message", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_generation_jobs_project_id", "generation_jobs", ["project_id"])
    op.create_index("ix_generation_jobs_celery_task_id", "generation_jobs", ["celery_task_id"])


def downgrade() -> None:
    op.drop_table("generation_jobs")
    op.drop_table("assets")
    op.drop_table("projects")
    op.drop_table("users")
    for enum_name in ("job_status", "job_stage", "asset_type", "project_status", "content_tone"):
        postgresql.ENUM(name=enum_name).drop(op.get_bind(), checkfirst=True)
