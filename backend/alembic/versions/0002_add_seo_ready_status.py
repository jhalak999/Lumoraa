"""add seo_ready project status

Revision ID: 0002_add_seo_ready_status
Revises: 0001_initial
Create Date: 2026-07-17 22:40:00
"""

from alembic import op

revision = "0002_add_seo_ready_status"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN\n"
        "IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typname = 'project_status' AND e.enumlabel = 'seo_ready') THEN\n"
        "ALTER TYPE project_status ADD VALUE 'seo_ready';\n"
        "END IF;\n"
        "END $$;"
    )


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely.
    pass
