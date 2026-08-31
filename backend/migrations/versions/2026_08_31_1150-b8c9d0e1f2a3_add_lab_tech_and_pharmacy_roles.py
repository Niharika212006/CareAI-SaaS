"""Add LAB_TECHNICIAN and PHARMACY_STAFF roles to UserRole enum.

Revision ID: b8c9d0e1f2a3
Revises: a1b2c3d4e5f6
Create Date: 2026-08-31 11:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8c9d0e1f2a3'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # In SQLite, Enums are stored as VARCHAR and validated at the application/SQLAlchemy layer.
    # In PostgreSQL, this handles adding new enum values if PostgreSQL is used.
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'LAB_TECHNICIAN'")
            op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PHARMACY_STAFF'")


def downgrade() -> None:
    pass
