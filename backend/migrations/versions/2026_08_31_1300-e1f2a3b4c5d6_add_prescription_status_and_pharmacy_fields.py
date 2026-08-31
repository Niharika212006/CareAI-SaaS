"""add prescription status and pharmacy fields

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-08-31 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('prescriptions')]

    with op.batch_alter_table('prescriptions', schema=None) as batch_op:
        if 'status' not in columns:
            batch_op.add_column(
                sa.Column(
                    'status',
                    sa.String(length=50),
                    nullable=False,
                    server_default='PRESCRIBED',
                )
            )
            batch_op.create_index(batch_op.f('ix_prescriptions_status'), ['status'], unique=False)

        if 'pharmacy_notes' not in columns:
            batch_op.add_column(sa.Column('pharmacy_notes', sa.Text(), nullable=True))

        if 'dispensed_at' not in columns:
            batch_op.add_column(sa.Column('dispensed_at', sa.DateTime(), nullable=True))

        if 'dispensed_by_user_id' not in columns:
            batch_op.add_column(sa.Column('dispensed_by_user_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                'fk_prescriptions_dispensed_by_user_id',
                'users',
                ['dispensed_by_user_id'],
                ['id'],
                ondelete='SET NULL',
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('prescriptions')]

    with op.batch_alter_table('prescriptions', schema=None) as batch_op:
        if 'dispensed_by_user_id' in columns:
            batch_op.drop_constraint('fk_prescriptions_dispensed_by_user_id', type_='foreignkey')
            batch_op.drop_column('dispensed_by_user_id')
        if 'dispensed_at' in columns:
            batch_op.drop_column('dispensed_at')
        if 'pharmacy_notes' in columns:
            batch_op.drop_column('pharmacy_notes')
        if 'status' in columns:
            batch_op.drop_index(batch_op.f('ix_prescriptions_status'))
            batch_op.drop_column('status')
