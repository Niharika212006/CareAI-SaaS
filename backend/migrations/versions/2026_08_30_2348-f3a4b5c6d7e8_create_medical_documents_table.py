"""create_medical_documents_table

Revision ID: f3a4b5c6d7e8
Revises: e2b3c4d5e6f7
Create Date: 2026-08-30 23:48:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, None] = 'e2b3c4d5e6f7'
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

    ensure_enum('documenttype', ['LAB_REPORT', 'IMAGING', 'PRESCRIPTION', 'DISCHARGE_SUMMARY', 'MEDICAL_CERTIFICATE', 'OTHER'])

    if 'medical_documents' not in tables:
        op.create_table(
            'medical_documents',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('patient_id', sa.Integer(), nullable=False),
            sa.Column('uploaded_by_user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column(
                'document_type',
                sa.Enum(
                    'LAB_REPORT',
                    'IMAGING',
                    'PRESCRIPTION',
                    'DISCHARGE_SUMMARY',
                    'MEDICAL_CERTIFICATE',
                    'OTHER',
                    name='documenttype',
                    create_type=False,
                ),
                nullable=False,
                server_default='OTHER',
            ),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('storage_key', sa.String(length=500), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['patient_id'], ['patient_profiles.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_medical_documents_patient_id'), 'medical_documents', ['patient_id'], unique=False)
        op.create_index(op.f('ix_medical_documents_uploaded_by_user_id'), 'medical_documents', ['uploaded_by_user_id'], unique=False)
        op.create_index(op.f('ix_medical_documents_document_type'), 'medical_documents', ['document_type'], unique=False)
        op.create_index(op.f('ix_medical_documents_storage_key'), 'medical_documents', ['storage_key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_medical_documents_storage_key'), table_name='medical_documents')
    op.drop_index(op.f('ix_medical_documents_document_type'), table_name='medical_documents')
    op.drop_index(op.f('ix_medical_documents_uploaded_by_user_id'), table_name='medical_documents')
    op.drop_index(op.f('ix_medical_documents_patient_id'), table_name='medical_documents')
    op.drop_table('medical_documents')
