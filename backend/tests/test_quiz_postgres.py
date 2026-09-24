import os
import uuid

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.course import Course
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.quiz import QuizAttemptAnswer
from app.models.user import User, UserRole
from app.schemas.quiz import AttemptSubmitRequest, GeneratedQuiz, QuizGenerateRequest
from app.services.quiz import generate_quiz, list_student_attempts, start_attempt, submit_attempt

pytestmark = pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1 for PostgreSQL quiz tests")


class FakeQuizGenerator:
    def generate_quiz(self, **kwargs):
        assert "untrusted reference data" in kwargs["input_text"]
        return GeneratedQuiz.model_validate({"questions": [{
            "question_text": "Which learning uses labels?", "explanation": "The lesson says supervised learning uses labels.",
            "options": [
                {"option_text": "Supervised learning", "is_correct": True},
                {"option_text": "Clustering", "is_correct": False},
                {"option_text": "Random guessing", "is_correct": False},
                {"option_text": "None", "is_correct": False},
            ],
        }]})


def test_quiz_schema_constraints_and_types():
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    try:
        expected = {"quizzes", "quiz_questions", "quiz_options", "quiz_attempts", "quiz_attempt_answers"}
        assert expected <= set(inspector.get_table_names())
        for table in expected:
            id_column = next(c for c in inspector.get_columns(table) if c["name"] == "id")
            assert "UUID" in str(id_column["type"]).upper()
        attempt_columns = {c["name"]: c for c in inspector.get_columns("quiz_attempts")}
        assert attempt_columns["started_at"]["type"].timezone is True
        assert attempt_columns["submitted_at"]["type"].timezone is True
        assert {u["name"] for u in inspector.get_unique_constraints("quiz_attempt_answers")} == {"uq_quiz_attempt_answers_attempt_question"}
        checks = {c["name"] for c in inspector.get_check_constraints("quiz_attempts")}
        assert {"ck_quiz_attempts_total_positive", "ck_quiz_attempts_correct_range", "ck_quiz_attempts_score_range", "ck_quiz_attempts_submission_state"} <= checks
        quiz_fks = {fk["name"]: fk for fk in inspector.get_foreign_keys("quizzes")}
        assert all(fk["options"].get("ondelete") == "RESTRICT" for fk in quiz_fks.values())
    finally:
        engine.dispose()


def test_postgres_fake_generation_attempt_grading_and_history():
    engine = create_engine(settings.database_url)
    connection = engine.connect(); transaction = connection.begin(); db = Session(bind=connection)
    try:
        teacher = User(id=uuid.uuid4(), name="PG Quiz Teacher", email=f"pgqt-{uuid.uuid4()}@example.com", password_hash="unused", role=UserRole.TEACHER)
        student = User(id=uuid.uuid4(), name="PG Quiz Student", email=f"pgqs-{uuid.uuid4()}@example.com", password_hash="unused", role=UserRole.STUDENT)
        course = Course(id=uuid.uuid4(), teacher_id=teacher.id, title="PG Quiz Course")
        lesson = Lesson(id=uuid.uuid4(), course_id=course.id, title="PG Quiz Lesson", position=1)
        db.add_all([teacher, student, course, lesson]); db.flush()
        document = Document(id=uuid.uuid4(), lesson_id=lesson.id, uploaded_by=teacher.id, original_filename="pg-lesson.pdf", content_type="application/pdf", file_size=1, storage_path=f"{uuid.uuid4()}.pdf", status=DocumentStatus.READY)
        document.chunks.append(DocumentChunk(chunk_index=0, content="Supervised learning uses labeled examples.", embedding=[1.0] + [0.0] * 1535))
        db.add_all([document, Enrollment(student_id=student.id, course_id=course.id)]); db.flush()

        quiz = generate_quiz(db, lesson, teacher, QuizGenerateRequest(title="PG Generated Quiz", question_count=1), FakeQuizGenerator(), 2000)
        attempt = start_attempt(db, quiz, student)
        question = quiz.questions[0]; correct = next(option for option in question.options if option.is_correct)
        submission = AttemptSubmitRequest.model_validate({"answers": [{"question_id": question.id, "selected_option_id": correct.id}]})
        attempt, review = submit_attempt(db, attempt, submission)

        assert attempt.correct_count == 1 and str(attempt.score_percent) == "100.00"
        assert len(review) == 1 and review[0][3] is True
        answer = db.scalar(select(QuizAttemptAnswer).where(QuizAttemptAnswer.attempt_id == attempt.id))
        assert answer.is_correct is True and answer.selected_option_id == correct.id
        assert [item.id for item in list_student_attempts(db, student.id)] == [attempt.id]
    finally:
        db.close(); transaction.rollback(); connection.close(); engine.dispose()
