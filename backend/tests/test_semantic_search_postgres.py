import os
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.course import Course
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.lesson import Lesson
from app.models.user import User, UserRole
from app.services.search import search_lesson_chunks
from app.services.tutor import answer_lesson_question

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1",
    reason="Set RUN_POSTGRES_TESTS=1 to run pgvector integration tests",
)


def vector(first: float, second: float = 0.0) -> list[float]:
    return [first, second] + [0.0] * 1534


def test_exact_cosine_search_scope_filters_and_ordering() -> None:
    engine = create_engine(settings.database_url)
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)
    try:
        teacher = User(
            id=uuid.uuid4(),
            name="Vector Teacher",
            email=f"vector-{uuid.uuid4()}@example.com",
            password_hash="not-used",
            role=UserRole.TEACHER,
        )
        course = Course(id=uuid.uuid4(), teacher_id=teacher.id, title="Vector Course")
        lesson = Lesson(
            id=uuid.uuid4(), course_id=course.id, title="Target", position=1
        )
        other_lesson = Lesson(
            id=uuid.uuid4(), course_id=course.id, title="Other", position=2
        )
        db.add_all([teacher, course, lesson, other_lesson])
        db.flush()

        first_document = Document(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            lesson_id=lesson.id,
            uploaded_by=teacher.id,
            original_filename="first.pdf",
            content_type="application/pdf",
            file_size=1,
            storage_path=f"{uuid.uuid4().hex}.pdf",
            status=DocumentStatus.READY,
        )
        second_document = Document(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            lesson_id=lesson.id,
            uploaded_by=teacher.id,
            original_filename="second.pdf",
            content_type="application/pdf",
            file_size=1,
            storage_path=f"{uuid.uuid4().hex}.pdf",
            status=DocumentStatus.READY,
        )
        failed_document = Document(
            id=uuid.uuid4(),
            lesson_id=lesson.id,
            uploaded_by=teacher.id,
            original_filename="failed.pdf",
            content_type="application/pdf",
            file_size=1,
            storage_path=f"{uuid.uuid4().hex}.pdf",
            status=DocumentStatus.FAILED,
        )
        other_lesson_document = Document(
            id=uuid.uuid4(),
            lesson_id=other_lesson.id,
            uploaded_by=teacher.id,
            original_filename="other.pdf",
            content_type="application/pdf",
            file_size=1,
            storage_path=f"{uuid.uuid4().hex}.pdf",
            status=DocumentStatus.READY,
        )
        db.add_all(
            [first_document, second_document, failed_document, other_lesson_document]
        )
        db.flush()
        db.add_all(
            [
                DocumentChunk(
                    document_id=first_document.id,
                    chunk_index=0,
                    content="exact",
                    embedding=vector(1.0),
                ),
                DocumentChunk(
                    document_id=first_document.id,
                    chunk_index=1,
                    content="tie first",
                    embedding=vector(0.8, 0.6),
                ),
                DocumentChunk(
                    document_id=second_document.id,
                    chunk_index=0,
                    content="tie second",
                    embedding=vector(0.8, 0.6),
                ),
                DocumentChunk(
                    document_id=second_document.id,
                    chunk_index=1,
                    content="null embedding",
                    embedding=None,
                ),
                DocumentChunk(
                    document_id=failed_document.id,
                    chunk_index=0,
                    content="failed exact",
                    embedding=vector(1.0),
                ),
                DocumentChunk(
                    document_id=other_lesson_document.id,
                    chunk_index=0,
                    content="other lesson exact",
                    embedding=vector(1.0),
                ),
            ]
        )
        db.flush()

        matches = search_lesson_chunks(db, lesson.id, vector(1.0), limit=10)

        assert [match.content for match in matches] == [
            "exact",
            "tie first",
            "tie second",
        ]
        assert matches[0].similarity == pytest.approx(1.0)
        assert matches[1].similarity == pytest.approx(0.8)
        assert matches[2].similarity == pytest.approx(0.8)
    finally:
        db.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def test_postgres_grounded_tutor_flow_is_scoped_to_lesson() -> None:
    engine = create_engine(settings.database_url)
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)

    class FakeEmbedding:
        def embed_text(self, text: str) -> list[float]:
            assert text == "What is grounded retrieval?"
            return vector(1.0)

    class FakeAnswer:
        def __init__(self) -> None:
            self.calls = []

        def generate_answer(self, *, instructions: str, input_text: str) -> str:
            self.calls.append((instructions, input_text))
            return "Grounded retrieval uses the selected lesson material."

    try:
        teacher = User(
            id=uuid.uuid4(),
            name="RAG Teacher",
            email=f"rag-{uuid.uuid4()}@example.com",
            password_hash="not-used",
            role=UserRole.TEACHER,
        )
        course = Course(id=uuid.uuid4(), teacher_id=teacher.id, title="RAG Course")
        lesson = Lesson(id=uuid.uuid4(), course_id=course.id, title="Target", position=1)
        other_lesson = Lesson(id=uuid.uuid4(), course_id=course.id, title="Other", position=2)
        db.add_all([teacher, course, lesson, other_lesson])
        db.flush()

        target_document = Document(
            id=uuid.uuid4(), lesson_id=lesson.id, uploaded_by=teacher.id,
            original_filename="target.pdf", content_type="application/pdf", file_size=1,
            storage_path=f"{uuid.uuid4().hex}.pdf", status=DocumentStatus.READY,
        )
        other_document = Document(
            id=uuid.uuid4(), lesson_id=other_lesson.id, uploaded_by=teacher.id,
            original_filename="other.pdf", content_type="application/pdf", file_size=1,
            storage_path=f"{uuid.uuid4().hex}.pdf", status=DocumentStatus.READY,
        )
        db.add_all([target_document, other_document])
        db.flush()
        db.add_all([
            DocumentChunk(
                document_id=target_document.id, chunk_index=0,
                content="Grounded retrieval uses selected lesson material.", embedding=vector(1.0),
            ),
            DocumentChunk(
                document_id=other_document.id, chunk_index=0,
                content="CROSS-LESSON SECRET", embedding=vector(1.0),
            ),
        ])
        db.flush()

        answer_service = FakeAnswer()
        result = answer_lesson_question(
            db=db,
            lesson_id=lesson.id,
            question="What is grounded retrieval?",
            embedding_service=FakeEmbedding(),
            answer_service=answer_service,
            retrieval_top_k=5,
            max_context_characters=2000,
        )

        assert result.answer == "Grounded retrieval uses the selected lesson material."
        assert [(source.document_id, source.chunk_index) for source in result.sources] == [
            (target_document.id, 0)
        ]
        assert len(answer_service.calls) == 1
        assert "target.pdf" in answer_service.calls[0][1]
        assert "CROSS-LESSON SECRET" not in answer_service.calls[0][1]
    finally:
        db.close()
        transaction.rollback()
        connection.close()
        engine.dispose()
