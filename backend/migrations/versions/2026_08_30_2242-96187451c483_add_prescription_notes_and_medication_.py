"""add_prescription_notes_and_medication_fields

Revision ID: 96187451c483
Revises: 16b58d05d2d2
Create Date: 2026-08-30 22:42:58.309408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96187451c483'
down_revision: Union[str, None] = '16b58d05d2d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check prescription_items columns
    item_cols = [c['name'] for c in inspector.get_columns('prescription_items')]
    if 'medication_name' not in item_cols:
        op.add_column('prescription_items', sa.Column('medication_name', sa.String(length=200), nullable=True))
    if 'route_of_administration' not in item_cols:
        op.add_column('prescription_items', sa.Column('route_of_administration', sa.String(length=100), nullable=True))

    # Check prescriptions columns
    pres_cols = [c['name'] for c in inspector.get_columns('prescriptions')]
    if 'notes' not in pres_cols:
        op.add_column('prescriptions', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    pass

