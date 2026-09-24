import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.quiz import Quiz, QuizAttempt, QuizAttemptAnswer, QuizOption, QuizQuestion
from app.models.user import User

PASSWORD = "correct-horse-battery-staple"


def register(client, email, role):
    client.post("/api/v1/auth/register", json={"name": email.split("@")[0], "email": email, "password": PASSWORD, "role": role})
    token = client.post("/api/v1/auth/login", data={"username": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def user(db, email):
    return db.scalar(select(User).where(User.email == email))


def add_quiz(db, lesson, teacher, title, question_count):
    quiz = Quiz(id=uuid.uuid4(), lesson_id=lesson.id, created_by=teacher.id, title=title)
    for position in range(1, question_count + 1):
        question = QuizQuestion(id=uuid.uuid4(), question_text=f"{title} question {position}", explanation="Explanation", position=position)
        question.options = [
            QuizOption(id=uuid.uuid4(), option_text="Correct", is_correct=True, position=1),
            QuizOption(id=uuid.uuid4(), option_text="Wrong A", is_correct=False, position=2),
            QuizOption(id=uuid.uuid4(), option_text="Wrong B", is_correct=False, position=3),
            QuizOption(id=uuid.uuid4(), option_text="Wrong C", is_correct=False, position=4),
        ]
        quiz.questions.append(question)
    db.add(quiz); db.flush(); return quiz


def add_attempt(db, quiz, student, correct_count, submitted_at, attempt_id=None, add_answers=True):
    total = len(quiz.questions)
    score = None if submitted_at is None else (Decimal(correct_count) * 100 / Decimal(total)).quantize(Decimal("0.01"))
    attempt = QuizAttempt(id=attempt_id or uuid.uuid4(), quiz_id=quiz.id, student_id=student.id,
        correct_count=correct_count if submitted_at else None, total_questions=total,
        score_percent=score, submitted_at=submitted_at)
    db.add(attempt); db.flush()
    if add_answers:
        for index, question in enumerate(quiz.questions):
            is_correct = index < correct_count
            selected = question.options[0] if is_correct else question.options[1]
            db.add(QuizAttemptAnswer(attempt_id=attempt.id, question_id=question.id, selected_option_id=selected.id, is_correct=is_correct))
    db.flush(); return attempt


def analytics_data(client: TestClient, db: Session):
    owner_headers = register(client, "analytics-owner@example.com", "teacher")
    other_teacher_headers = register(client, "analytics-other-teacher@example.com", "teacher")
    student_headers = register(client, "analytics-student@example.com", "student")
    zero_headers = register(client, "analytics-zero@example.com", "student")
    outsider_headers = register(client, "analytics-outsider@example.com", "student")
    owner, other_teacher = user(db, "analytics-owner@example.com"), user(db, "analytics-other-teacher@example.com")
    student, zero, outsider = user(db, "analytics-student@example.com"), user(db, "analytics-zero@example.com"), user(db, "analytics-outsider@example.com")
    course = Course(id=uuid.uuid4(), teacher_id=owner.id, title="Analytics Course")
    other_course = Course(id=uuid.uuid4(), teacher_id=other_teacher.id, title="Other Course")
    lesson1 = Lesson(id=uuid.uuid4(), course_id=course.id, title="Lesson One", position=1)
    lesson2 = Lesson(id=uuid.uuid4(), course_id=course.id, title="Lesson Two", position=2)
    other_lesson = Lesson(id=uuid.uuid4(), course_id=other_course.id, title="Other Lesson", position=1)
    db.add_all([course, other_course, lesson1, lesson2, other_lesson]); db.flush()
    db.add_all([Enrollment(student_id=student.id, course_id=course.id), Enrollment(student_id=zero.id, course_id=course.id), Enrollment(student_id=outsider.id, course_id=other_course.id)])
    quiz1 = add_quiz(db, lesson1, owner, "One Question", 1)
    quiz2 = add_quiz(db, lesson2, owner, "Three Questions", 3)
    unused_quiz = add_quiz(db, lesson2, owner, "Unused Quiz", 1)
    other_quiz = add_quiz(db, other_lesson, other_teacher, "Other Quiz", 1)
    moment = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    first_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    second_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    add_attempt(db, quiz1, student, 1, moment, first_id)
    add_attempt(db, quiz2, student, 1, moment, second_id)
    add_attempt(db, unused_quiz, student, 1, None)
    add_attempt(db, other_quiz, outsider, 1, moment)
    db.commit()
    return locals()


def test_analytics_authorization(client, db_session):
    data = analytics_data(client, db_session)
    assert client.get("/api/v1/users/me/analytics").status_code == 401
    assert client.get("/api/v1/users/me/analytics", headers=data["owner_headers"]).status_code == 403
    assert client.get(f"/api/v1/courses/{data['course'].id}/analytics").status_code == 401
    assert client.get(f"/api/v1/courses/{data['course'].id}/analytics", headers=data["student_headers"]).status_code == 403
    assert client.get(f"/api/v1/courses/{data['course'].id}/analytics", headers=data["other_teacher_headers"]).status_code == 403


def test_student_overview_empty_and_weighted_accuracy(client, db_session):
    data = analytics_data(client, db_session)
    overview = client.get("/api/v1/users/me/analytics", headers=data["student_headers"]).json()
    assert overview == {
        "total_submitted_attempts": 2, "distinct_quizzes_attempted": 2, "distinct_lessons_practiced": 2,
        "average_score": "66.67", "best_score": "100.00", "total_questions_answered": 4,
        "total_correct_answers": 2, "overall_accuracy_percent": "50.00",
    }
    empty = client.get("/api/v1/users/me/analytics", headers=data["zero_headers"]).json()
    assert empty["total_submitted_attempts"] == 0
    assert empty["average_score"] is None and empty["overall_accuracy_percent"] is None
    outsider = client.get("/api/v1/users/me/analytics", headers=data["outsider_headers"]).json()
    assert outsider["total_submitted_attempts"] == 1


def test_student_lesson_and_progress_ordering(client, db_session):
    data = analytics_data(client, db_session)
    lessons = client.get("/api/v1/users/me/analytics/lessons", headers=data["student_headers"]).json()
    assert [item["lesson_title"] for item in lessons] == ["Lesson One", "Lesson Two"]
    assert [item["accuracy_percent"] for item in lessons] == ["100.00", "33.33"]
    progress = client.get("/api/v1/users/me/analytics/progress", headers=data["student_headers"]).json()
    assert [item["attempt_id"] for item in progress] == [
        "00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"
    ]
    assert all(item["submitted_at"] is not None for item in progress)


def test_teacher_course_student_lesson_and_question_analytics(client, db_session):
    data = analytics_data(client, db_session)
    base = f"/api/v1/courses/{data['course'].id}/analytics"
    overview = client.get(base, headers=data["owner_headers"]).json()
    assert overview["enrolled_students"] == 2
    assert overview["students_with_submitted_attempts"] == 1
    assert overview["total_submitted_attempts"] == 2
    assert overview["average_score"] == "66.67"
    assert overview["overall_accuracy_percent"] == "50.00"
    students = client.get(base + "/students", headers=data["owner_headers"]).json()
    assert len(students) == 2
    by_name = {item["student_name"]: item for item in students}
    assert by_name["analytics-zero"]["submitted_attempts"] == 0
    assert by_name["analytics-zero"]["average_score"] is None
    assert by_name["analytics-student"]["accuracy_percent"] == "50.00"
    lessons = client.get(base + "/lessons", headers=data["owner_headers"]).json()
    assert [item["quizzes"] for item in lessons] == [1, 2]
    assert [item["submitted_attempts"] for item in lessons] == [1, 1]
    questions = client.get(base + "/questions", headers=data["owner_headers"]).json()
    assert len(questions) == 5
    assert sum(item["total_answers"] for item in questions) == 4
    assert any(item["total_answers"] == 0 and item["accuracy_percent"] is None for item in questions)
    serialized = str(overview) + str(students) + str(lessons) + str(questions)
    assert "Other Course" not in serialized and "analytics-outsider" not in serialized
    assert "storage_path" not in serialized and "embedding" not in serialized
