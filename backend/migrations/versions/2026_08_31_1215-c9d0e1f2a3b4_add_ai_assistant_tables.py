"""add ai assistant conversations and messages tables

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-08-31 12:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Create ai_conversations table if not exists
    if 'ai_conversations' not in tables:
        op.create_table(
            'ai_conversations',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column(
                'role',
                sa.Enum('PATIENT', 'DOCTOR', 'ADMIN', 'LAB_TECHNICIAN', 'PHARMACY_STAFF', name='userrole'),
                nullable=False,
            ),
            sa.Column('title', sa.String(length=255), nullable=False, server_default='New Conversation'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_ai_conversations_id'), 'ai_conversations', ['id'], unique=False)
        op.create_index(op.f('ix_ai_conversations_user_id'), 'ai_conversations', ['user_id'], unique=False)
        op.create_index(op.f('ix_ai_conversations_role'), 'ai_conversations', ['role'], unique=False)

    # 2. Create ai_messages table if not exists
    if 'ai_messages' not in tables:
        op.create_table(
            'ai_messages',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('conversation_id', sa.Integer(), nullable=False),
            sa.Column('sender', sa.String(length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('model_name', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_ai_messages_id'), 'ai_messages', ['id'], unique=False)
        op.create_index(op.f('ix_ai_messages_conversation_id'), 'ai_messages', ['conversation_id'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'ai_messages' in tables:
        op.drop_index(op.f('ix_ai_messages_conversation_id'), table_name='ai_messages')
        op.drop_index(op.f('ix_ai_messages_id'), table_name='ai_messages')
        op.drop_table('ai_messages')

    if 'ai_conversations' in tables:
        op.drop_index(op.f('ix_ai_conversations_role'), table_name='ai_conversations')
        op.drop_index(op.f('ix_ai_conversations_user_id'), table_name='ai_conversations')
        op.drop_index(op.f('ix_ai_conversations_id'), table_name='ai_conversations')
        op.drop_table('ai_conversations')
