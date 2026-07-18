"""
Import every model here so Alembic's `target_metadata = Base.metadata`
picks them all up for autogenerate, and so `Base.metadata.create_all`
(used in tests) creates the full schema.
"""
from app.models.asset import Asset, AssetType  # noqa: F401
from app.models.job import GenerationJob, JobStage, JobStatus  # noqa: F401
from app.models.project import ContentTone, Project, ProjectStatus  # noqa: F401
from app.models.user import User  # noqa: F401
