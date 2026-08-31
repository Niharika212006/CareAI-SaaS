"""create_medical_document_analyses_table

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d7e8
Create Date: 2026-08-30 23:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'medical_document_analyses' not in tables:
        op.create_table(
            'medical_document_analyses',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('document_id', sa.Integer(), nullable=False),
            sa.Column('requested_by_user_id', sa.Integer(), nullable=False),
            sa.Column('extracted_text', sa.Text(), nullable=True),
            sa.Column('summary', sa.Text(), nullable=False),
            sa.Column('document_category', sa.String(length=100), nullable=True),
            sa.Column('key_findings', sa.JSON(), nullable=True),
            sa.Column('detected_medications', sa.JSON(), nullable=True),
            sa.Column('detected_test_values', sa.JSON(), nullable=True),
            sa.Column('potential_concerns', sa.JSON(), nullable=True),
            sa.Column('patient_friendly_explanation', sa.Text(), nullable=True),
            sa.Column('recommended_next_step', sa.Text(), nullable=True),
            sa.Column('disclaimer', sa.Text(), nullable=False),
            sa.Column(
                'analysis_status',
                sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'),
                nullable=False,
                server_default='COMPLETED',
            ),
            sa.Column('ai_model_name', sa.String(length=100), nullable=False, server_default='CareAI-Clinical-Insight-v1'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['document_id'], ['medical_documents.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_medical_document_analyses_document_id'), 'medical_document_analyses', ['document_id'], unique=False)
        op.create_index(op.f('ix_medical_document_analyses_requested_by_user_id'), 'medical_document_analyses', ['requested_by_user_id'], unique=False)
        op.create_index(op.f('ix_medical_document_analyses_analysis_status'), 'medical_document_analyses', ['analysis_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_medical_document_analyses_analysis_status'), table_name='medical_document_analyses')
    op.drop_index(op.f('ix_medical_document_analyses_requested_by_user_id'), table_name='medical_document_analyses')
    op.drop_index(op.f('ix_medical_document_analyses_document_id'), table_name='medical_document_analyses')
    op.drop_table('medical_document_analyses')
