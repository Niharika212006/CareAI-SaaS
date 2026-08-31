"""create_notifications_table

Revision ID: e2b3c4d5e6f7
Revises: 7d9af077ad26
Create Date: 2026-08-30 23:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e2b3c4d5e6f7'
down_revision: Union[str, None] = '7d9af077ad26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if bind.engine.name == "postgresql":
        postgresql.ENUM('APPOINTMENT', 'PRESCRIPTION', 'DOCTOR_APPROVAL', 'AI_SAFETY', 'SYSTEM', name='notificationtype').create(bind, checkfirst=True)
        postgresql.ENUM('LOW', 'NORMAL', 'HIGH', 'CRITICAL', name='notificationpriority').create(bind, checkfirst=True)

    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column(
                'notification_type',
                postgresql.ENUM('APPOINTMENT', 'PRESCRIPTION', 'DOCTOR_APPROVAL', 'AI_SAFETY', 'SYSTEM', name='notificationtype', create_type=False),
                nullable=False,
                server_default='SYSTEM',
            ),
            sa.Column(
                'priority',
                postgresql.ENUM('LOW', 'NORMAL', 'HIGH', 'CRITICAL', name='notificationpriority', create_type=False),
                nullable=False,
                server_default='NORMAL',
            ),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
        op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
        op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
        op.create_index(op.f('ix_notifications_priority'), 'notifications', ['priority'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_notifications_priority'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_notification_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')
