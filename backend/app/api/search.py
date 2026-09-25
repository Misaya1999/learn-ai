from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DatabaseSession, LessonMaterialAccess
from app.schemas.search import SemanticSearchRequest, SemanticSearchResult
from app.services.embedding import (
    EmbeddingService,
    EmbeddingServiceError,
    get_embedding_service,
)
from app.services.search import search_lesson_chunks

router = APIRouter(tags=["semantic search"])
SearchEmbeddingService = Annotated[EmbeddingService, Depends(get_embedding_service)]


@router.post(
    "/lessons/{lesson_id}/search", response_model=list[SemanticSearchResult]
)
def semantic_search(
    request: SemanticSearchRequest,
    db: DatabaseSession,
    lesson: LessonMaterialAccess,
    embedding_service: SearchEmbeddingService,
) -> list[SemanticSearchResult]:
    try:
        query_embedding = embedding_service.embed_text(request.query)
    except (EmbeddingServiceError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate query embedding",
        ) from None
    return search_lesson_chunks(db, lesson.id, query_embedding, request.limit)
