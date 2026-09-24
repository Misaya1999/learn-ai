"""Add pgvector embeddings to document chunks.

Revision ID: 20260924_04
Revises: 20260924_03
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "20260924_04"
down_revision: str | None = "20260924_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "document_chunks",
        sa.Column("embedding", Vector(1536), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("document_chunks", "embedding")
