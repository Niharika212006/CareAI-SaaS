"""create rag knowledge tables

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-09-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect_name = conn.dialect.name

    # Enable pgvector extension if running on PostgreSQL
    if dialect_name == "postgresql":
        try:
            op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception:
            pass

    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # 1. Create knowledge_documents table
    if "knowledge_documents" not in tables:
        op.create_table(
            "knowledge_documents",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("document_name", sa.String(length=255), nullable=False),
            sa.Column("document_type", sa.String(length=100), nullable=False, server_default="OTHER"),
            sa.Column("source", sa.String(length=255), nullable=True),
            sa.Column("patient_id", sa.Integer(), nullable=True),
            sa.Column("medical_document_id", sa.Integer(), nullable=True),
            sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
            sa.Column("allowed_roles", sa.JSON(), nullable=True),
            sa.Column("document_date", sa.DateTime(), nullable=True),
            sa.Column("doc_metadata", sa.JSON(), nullable=True),
            sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["medical_document_id"], ["medical_documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_knowledge_documents_id"), "knowledge_documents", ["id"], unique=False)
        op.create_index(op.f("ix_knowledge_documents_document_name"), "knowledge_documents", ["document_name"], unique=False)
        op.create_index(op.f("ix_knowledge_documents_document_type"), "knowledge_documents", ["document_type"], unique=False)
        op.create_index(op.f("ix_knowledge_documents_patient_id"), "knowledge_documents", ["patient_id"], unique=False)
        op.create_index(op.f("ix_knowledge_documents_medical_document_id"), "knowledge_documents", ["medical_document_id"], unique=False)
        op.create_index(op.f("ix_knowledge_documents_uploaded_by_user_id"), "knowledge_documents", ["uploaded_by_user_id"], unique=False)
        op.create_index(op.f("ix_knowledge_documents_document_date"), "knowledge_documents", ["document_date"], unique=False)

    # 2. Create knowledge_chunks table
    if "knowledge_chunks" not in tables:
        op.create_table(
            "knowledge_chunks",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=False),
            sa.Column("chunk_index", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("page_number", sa.Integer(), nullable=True),
            sa.Column("embedding", Vector(384), nullable=True),
            sa.Column("chunk_metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_knowledge_chunks_id"), "knowledge_chunks", ["id"], unique=False)
        op.create_index(op.f("ix_knowledge_chunks_document_id"), "knowledge_chunks", ["document_id"], unique=False)
        op.create_index(op.f("ix_knowledge_chunks_page_number"), "knowledge_chunks", ["page_number"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "knowledge_chunks" in tables:
        op.drop_table("knowledge_chunks")
    if "knowledge_documents" in tables:
        op.drop_table("knowledge_documents")
