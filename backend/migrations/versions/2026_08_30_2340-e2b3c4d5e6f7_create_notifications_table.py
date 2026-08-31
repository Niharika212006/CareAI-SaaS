"""create_notifications_table

Revision ID: e2b3c4d5e6f7
Revises: 7d9af077ad26
Create Date: 2026-08-30 23:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2b3c4d5e6f7'
down_revision: Union[str, None] = '7d9af077ad26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def ensure_enum(enum_name: str, values: list) -> None:
    bind = op.get_bind()
    if bind.engine.name == "postgresql":
        with op.get_context().autocommit_block():
            check_sql = sa.text("SELECT 1 FROM pg_type WHERE typname = :name")
            exists = bind.execute(check_sql, {"name": enum_name}).scalar()
            if not exists:
                vals_str = ", ".join(f"'{v}'" for v in values)
                bind.execute(sa.text(f"CREATE TYPE {enum_name} AS ENUM ({vals_str})"))


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    ensure_enum('notificationtype', ['APPOINTMENT', 'PRESCRIPTION', 'DOCTOR_APPROVAL', 'AI_SAFETY', 'SYSTEM'])
    ensure_enum('notificationpriority', ['LOW', 'NORMAL', 'HIGH', 'CRITICAL'])

    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column(
                'notification_type',
                sa.Enum('APPOINTMENT', 'PRESCRIPTION', 'DOCTOR_APPROVAL', 'AI_SAFETY', 'SYSTEM', name='notificationtype', create_type=False),
                nullable=False,
                server_default='SYSTEM',
            ),
            sa.Column(
                'priority',
                sa.Enum('LOW', 'NORMAL', 'HIGH', 'CRITICAL', name='notificationpriority', create_type=False),
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
