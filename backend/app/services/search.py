import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk, DocumentStatus


@dataclass(frozen=True)
class SearchMatch:
    document_id: uuid.UUID
    original_filename: str
    chunk_index: int
    content: str
    similarity: float


def search_lesson_chunks(
    db: Session,
    lesson_id: uuid.UUID,
    query_embedding: list[float],
    limit: int,
) -> list[SearchMatch]:
    cosine_distance = DocumentChunk.embedding.cosine_distance(query_embedding).label(
        "cosine_distance"
    )
    statement = (
        select(
            DocumentChunk.document_id,
            Document.original_filename,
            DocumentChunk.chunk_index,
            DocumentChunk.content,
            cosine_distance,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.lesson_id == lesson_id,
            Document.status == DocumentStatus.READY,
            DocumentChunk.embedding.is_not(None),
        )
        .order_by(
            cosine_distance,
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            DocumentChunk.id,
        )
        .limit(limit)
    )
    rows = db.execute(statement).all()
    return [
        SearchMatch(
            document_id=row.document_id,
            original_filename=row.original_filename,
            chunk_index=row.chunk_index,
            content=row.content,
            similarity=1.0 - float(row.cosine_distance),
        )
        for row in rows
    ]
