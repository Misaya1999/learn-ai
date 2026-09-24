import os
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.user import User, UserRole
from app.services.analytics import (
    course_lessons, course_overview, course_questions, course_students,
    student_lessons, student_overview, student_progress,
)
from tests.test_analytics import add_attempt, add_quiz

pytestmark = pytest.mark.skipif(os.getenv("RUN_POSTGRES_TESTS") != "1", reason="Set RUN_POSTGRES_TESTS=1 for PostgreSQL analytics tests")


def test_postgres_learning_analytics_aggregations_and_isolation():
    engine = create_engine(settings.database_url)
    connection = engine.connect(); transaction = connection.begin(); db = Session(bind=connection)
    try:
        teacher = User(id=uuid.uuid4(), name="Analytics Teacher", email=f"pga-{uuid.uuid4()}@example.com", password_hash="unused", role=UserRole.TEACHER)
        other_teacher = User(id=uuid.uuid4(), name="Other Teacher", email=f"pgo-{uuid.uuid4()}@example.com", password_hash="unused", role=UserRole.TEACHER)
        student = User(id=uuid.uuid4(), name="Practicing Student", email=f"pgs-{uuid.uuid4()}@example.com", password_hash="unused", role=UserRole.STUDENT)
        zero = User(id=uuid.uuid4(), name="Zero Student", email=f"pgz-{uuid.uuid4()}@example.com", password_hash="unused", role=UserRole.STUDENT)
        other_student = User(id=uuid.uuid4(), name="Other Student", email=f"pgx-{uuid.uuid4()}@example.com", password_hash="unused", role=UserRole.STUDENT)
        course = Course(id=uuid.uuid4(), teacher_id=teacher.id, title="Analytics Course")
        other_course = Course(id=uuid.uuid4(), teacher_id=other_teacher.id, title="Isolated Course")
        lesson1 = Lesson(id=uuid.uuid4(), course_id=course.id, title="First", position=1)
        lesson2 = Lesson(id=uuid.uuid4(), course_id=course.id, title="Second", position=2)
        other_lesson = Lesson(id=uuid.uuid4(), course_id=other_course.id, title="Other", position=1)
        db.add_all([teacher, other_teacher, student, zero, other_student, course, other_course, lesson1, lesson2, other_lesson]); db.flush()
        db.add_all([Enrollment(student_id=student.id, course_id=course.id), Enrollment(student_id=zero.id, course_id=course.id), Enrollment(student_id=other_student.id, course_id=other_course.id)])
        quiz1, quiz2 = add_quiz(db, lesson1, teacher, "One", 1), add_quiz(db, lesson2, teacher, "Three", 3)
        unused = add_quiz(db, lesson2, teacher, "Unused", 1)
        other_quiz = add_quiz(db, other_lesson, other_teacher, "Other", 1)
        moment = datetime(2026, 2, 1, tzinfo=timezone.utc)
        add_attempt(db, quiz1, student, 1, moment)
        add_attempt(db, quiz2, student, 1, moment)
        add_attempt(db, unused, student, 1, None)
        add_attempt(db, other_quiz, other_student, 1, moment)
        db.flush()

        overview = student_overview(db, student.id)
        assert overview.total_submitted_attempts == 2
        assert str(overview.average_score) == "66.67"
        assert str(overview.overall_accuracy_percent) == "50.00"
        assert len(student_lessons(db, student.id)) == 2
        assert len(student_progress(db, student.id)) == 2
        course_metrics = course_overview(db, course.id)
        assert course_metrics.enrolled_students == 2
        assert course_metrics.students_with_submitted_attempts == 1
        assert str(course_metrics.overall_accuracy_percent) == "50.00"
        assert len(course_students(db, course.id)) == 2
        assert [row.submitted_attempts for row in course_lessons(db, course.id)] == [1, 1]
        questions = course_questions(db, course.id)
        assert len(questions) == 5 and sum(row.total_answers for row in questions) == 4
        assert all(row.quiz_id != other_quiz.id for row in questions)
    finally:
        db.close(); transaction.rollback(); connection.close(); engine.dispose()
