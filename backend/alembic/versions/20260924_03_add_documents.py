"""Add documents and document chunks.

Revision ID: 20260924_03
Revises: 20260924_02
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_03"
down_revision: str | None = "20260924_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

document_status = sa.Enum("processing", "ready", "failed", name="document_status")


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("file_size > 0", name="ck_documents_file_size_positive"),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lessons.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"], ["users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_path"),
    )
    op.create_index(op.f("ix_documents_lesson_id"), "documents", ["lesson_id"])
    op.create_index(op.f("ix_documents_uploaded_by"), "documents", ["uploaded_by"])

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(content)) > 0",
            name="ck_document_chunks_content_nonempty",
        ),
        sa.CheckConstraint(
            "chunk_index >= 0", name="ck_document_chunks_index_nonnegative"
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunks_document_index",
        ),
    )
    op.create_index(
        op.f("ix_document_chunks_document_id"),
        "document_chunks",
        ["document_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_document_chunks_document_id"), table_name="document_chunks"
    )
    op.drop_table("document_chunks")
    op.drop_index(op.f("ix_documents_uploaded_by"), table_name="documents")
    op.drop_index(op.f("ix_documents_lesson_id"), table_name="documents")
    op.drop_table("documents")
    if op.get_bind().dialect.name == "postgresql":
        document_status.drop(op.get_bind(), checkfirst=True)
