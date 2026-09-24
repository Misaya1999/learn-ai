import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.embedding import EmbeddingService
from app.services.llm import AnswerGenerationService
from app.services.rag import GROUNDING_INSTRUCTIONS, build_rag_context, build_tutor_input
from app.services.search import SearchMatch, search_lesson_chunks


INSUFFICIENT_CONTEXT_ANSWER = (
    "The available lesson material does not provide enough information to answer this question."
)


@dataclass(frozen=True)
class TutorAnswer:
    answer: str
    sources: tuple[SearchMatch, ...]


def answer_lesson_question(
    *,
    db: Session,
    lesson_id: uuid.UUID,
    question: str,
    embedding_service: EmbeddingService,
    answer_service: AnswerGenerationService,
    retrieval_top_k: int,
    max_context_characters: int,
) -> TutorAnswer:
    query_embedding = embedding_service.embed_text(question)
    matches = search_lesson_chunks(db, lesson_id, query_embedding, retrieval_top_k)
    context = build_rag_context(matches, max_context_characters)
    if not context.sources:
        return TutorAnswer(answer=INSUFFICIENT_CONTEXT_ANSWER, sources=())

    answer = answer_service.generate_answer(
        instructions=GROUNDING_INSTRUCTIONS,
        input_text=build_tutor_input(question, context.text),
    )
    return TutorAnswer(answer=answer, sources=context.sources)
