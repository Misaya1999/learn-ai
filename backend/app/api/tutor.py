from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import DatabaseSession, LessonMaterialAccess
from app.core.config import settings
from app.schemas.tutor import AnswerSource, AskQuestionRequest, AskQuestionResponse
from app.services.embedding import EmbeddingService, EmbeddingServiceError, get_embedding_service
from app.services.llm import AnswerGenerationService, LLMServiceError, get_answer_generation_service
from app.services.tutor import answer_lesson_question

router = APIRouter(tags=["AI tutor"])
TutorEmbeddingService = Annotated[EmbeddingService, Depends(get_embedding_service)]
TutorAnswerService = Annotated[
    AnswerGenerationService, Depends(get_answer_generation_service)
]


@router.post("/lessons/{lesson_id}/ask", response_model=AskQuestionResponse)
def ask_lesson_question(
    request: AskQuestionRequest,
    db: DatabaseSession,
    lesson: LessonMaterialAccess,
    embedding_service: TutorEmbeddingService,
    answer_service: TutorAnswerService,
) -> AskQuestionResponse:
    try:
        result = answer_lesson_question(
            db=db,
            lesson_id=lesson.id,
            question=request.question,
            embedding_service=embedding_service,
            answer_service=answer_service,
            retrieval_top_k=settings.ai_tutor_retrieval_top_k,
            max_context_characters=settings.ai_tutor_max_context_characters,
        )
    except (EmbeddingServiceError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve lesson context",
        ) from None
    except LLMServiceError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate tutor answer",
        ) from None
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve lesson context",
        ) from None

    return AskQuestionResponse(
        answer=result.answer,
        sources=[
            AnswerSource(
                document_id=source.document_id,
                filename=source.original_filename,
                chunk_index=source.chunk_index,
                similarity=source.similarity,
            )
            for source in result.sources
        ],
    )
