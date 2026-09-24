import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.main import app
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.quiz import Quiz, QuizAttemptAnswer, QuizQuestion
from app.schemas.quiz import GeneratedQuiz, GeneratedQuizQuestion
from app.services.quiz_generation import QuizGenerationProviderError, get_quiz_generation_service


PASSWORD = "correct-horse-battery-staple"


def auth(client, email, role):
    client.post("/api/v1/auth/register", json={"name": email, "email": email, "password": PASSWORD, "role": role})
    token = client.post("/api/v1/auth/login", data={"username": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def learning_setup(client, db, suffix="base", material=True):
    teacher = auth(client, f"teacher-{suffix}@example.com", "teacher")
    course = client.post("/api/v1/courses", json={"title": "Quiz Course"}, headers=teacher).json()
    lesson = client.post(f"/api/v1/courses/{course['id']}/lessons", json={"title": "Quiz Lesson", "position": 1}, headers=teacher).json()
    if material:
        from app.models.user import User
        user = db.scalar(select(User).where(User.email == f"teacher-{suffix}@example.com"))
        document = Document(lesson_id=uuid.UUID(lesson["id"]), uploaded_by=user.id, original_filename="lesson.pdf", content_type="application/pdf", file_size=10, storage_path=f"{uuid.uuid4()}.pdf", status=DocumentStatus.READY)
        document.chunks.append(DocumentChunk(chunk_index=0, content="Supervised learning uses labeled examples.", embedding=[1.0] + [0.0] * 1535))
        db.add(document); db.commit()
    return teacher, course, lesson


def generate(client, lesson, teacher, count=2):
    return client.post(f"/api/v1/lessons/{lesson['id']}/quizzes/generate", json={"title": "Generated Quiz", "question_count": count}, headers=teacher)


def student_and_enroll(client, course, suffix):
    headers = auth(client, f"student-{suffix}@example.com", "student")
    response = client.post(f"/api/v1/courses/{course['id']}/enroll", headers=headers)
    assert response.status_code == 201
    return headers


def test_teacher_generates_persisted_ordered_quiz(client: TestClient, db_session: Session):
    teacher, _, lesson = learning_setup(client, db_session, "generate")
    response = generate(client, lesson, teacher)
    assert response.status_code == 201
    data = response.json()
    assert [q["position"] for q in data["questions"]] == [1, 2]
    assert [o["position"] for o in data["questions"][0]["options"]] == [1, 2, 3, 4]
    assert sum(o["is_correct"] for o in data["questions"][0]["options"]) == 1
    assert db_session.scalar(select(func.count()).select_from(Quiz)) == 1
    assert db_session.scalar(select(func.count()).select_from(QuizQuestion)) == 2


def test_generation_authorization(client, db_session):
    teacher, _, lesson = learning_setup(client, db_session, "authz")
    other = auth(client, "other-teacher@example.com", "teacher")
    student = auth(client, "quiz-student@example.com", "student")
    assert generate(client, lesson, other).status_code == 403
    assert generate(client, lesson, student).status_code == 403
    assert client.post(f"/api/v1/lessons/{lesson['id']}/quizzes/generate", json={"title": "Q", "question_count": 2}).status_code == 401


def test_no_material_skips_provider(client, db_session):
    teacher, _, lesson = learning_setup(client, db_session, "empty", material=False)
    recorder = SimpleNamespace(calls=0)
    def fail_if_called(**kwargs): recorder.calls += 1; raise AssertionError
    recorder.generate_quiz = fail_if_called
    app.dependency_overrides[get_quiz_generation_service] = lambda: recorder
    response = generate(client, lesson, teacher)
    assert response.status_code == 422
    assert recorder.calls == 0
    assert db_session.scalar(select(func.count()).select_from(Quiz)) == 0


def test_provider_failures_and_invalid_output_leave_no_partial_quiz(client, db_session):
    teacher, _, lesson = learning_setup(client, db_session, "failures")
    class Broken:
        def generate_quiz(self, **kwargs): raise QuizGenerationProviderError("provider secret")
    app.dependency_overrides[get_quiz_generation_service] = Broken
    response = generate(client, lesson, teacher)
    assert response.status_code == 502 and "secret" not in response.text
    assert db_session.scalar(select(func.count()).select_from(Quiz)) == 0

    class Invalid:
        def generate_quiz(self, **kwargs):
            return SimpleNamespace(model_dump=lambda: {"questions": [{"question_text": "Q", "explanation": "E", "options": [
                {"option_text": "same", "is_correct": True}, {"option_text": " SAME ", "is_correct": True},
                {"option_text": "c", "is_correct": False}, {"option_text": "d", "is_correct": False}]}]})
    app.dependency_overrides[get_quiz_generation_service] = Invalid
    response = generate(client, lesson, teacher, count=1)
    assert response.status_code == 502
    assert db_session.scalar(select(func.count()).select_from(Quiz)) == 0


def test_provider_question_count_mismatch_leaves_no_quiz(client, db_session):
    teacher, _, lesson = learning_setup(client, db_session, "count-mismatch")
    from tests.conftest import FakeQuizGenerationService
    app.dependency_overrides[get_quiz_generation_service] = FakeQuizGenerationService
    response = generate(client, lesson, teacher, count=1)
    assert response.status_code == 502
    assert db_session.scalar(select(func.count()).select_from(Quiz)) == 0


@pytest.mark.parametrize("count", [0, 11])
def test_question_count_bounds(client, db_session, count):
    teacher, _, lesson = learning_setup(client, db_session, f"bounds-{count}")
    response = client.post(f"/api/v1/lessons/{lesson['id']}/quizzes/generate", json={"title": "Q", "question_count": count}, headers=teacher)
    assert response.status_code == 422


def test_student_view_hides_answer_key_and_attempt_start_requires_enrollment(client, db_session):
    teacher, course, lesson = learning_setup(client, db_session, "views")
    quiz = generate(client, lesson, teacher).json()
    enrolled = student_and_enroll(client, course, "enrolled")
    unenrolled = auth(client, "student-unenrolled@example.com", "student")
    teacher_start = client.post(f"/api/v1/quizzes/{quiz['id']}/attempts", headers=teacher)
    assert teacher_start.status_code == 403
    assert client.post(f"/api/v1/quizzes/{quiz['id']}/attempts", headers=unenrolled).status_code == 403
    view = client.get(f"/api/v1/quizzes/{quiz['id']}", headers=enrolled)
    assert view.status_code == 200
    assert "is_correct" not in view.text and "explanation" not in view.text
    started = client.post(f"/api/v1/quizzes/{quiz['id']}/attempts", headers=enrolled)
    assert started.status_code == 201
    assert "is_correct" not in started.text and "correct option" not in started.text.lower()


def test_submit_grades_server_side_persists_review_and_history(client, db_session):
    teacher, course, lesson = learning_setup(client, db_session, "grading")
    teacher_quiz = generate(client, lesson, teacher).json()
    student = student_and_enroll(client, course, "grader")
    start = client.post(f"/api/v1/quizzes/{teacher_quiz['id']}/attempts", headers=student).json()
    answers = []
    for index, question in enumerate(teacher_quiz["questions"]):
        correct = next(o for o in question["options"] if o["is_correct"])
        wrong = next(o for o in question["options"] if not o["is_correct"])
        answers.append({"question_id": question["id"], "selected_option_id": correct["id"] if index == 0 else wrong["id"]})
    response = client.post(f"/api/v1/quiz-attempts/{start['id']}/submit", json={"answers": answers}, headers=student)
    assert response.status_code == 200
    result = response.json()
    assert (result["correct_count"], result["total_questions"], result["score_percent"]) == (1, 2, "50.00")
    assert [item["is_correct"] for item in result["answers"]] == [True, False]
    assert all(item["correct_option_id"] and item["explanation"] for item in result["answers"])
    assert db_session.scalar(select(func.count()).select_from(QuizAttemptAnswer)) == 2
    history = client.get("/api/v1/users/me/quiz-attempts", headers=student)
    assert history.status_code == 200 and len(history.json()) == 1
    assert history.json()[0]["score_percent"] == "50.00"
    assert "storage_path" not in history.text and "embedding" not in history.text
    assert client.post(f"/api/v1/quiz-attempts/{start['id']}/submit", json={"answers": answers}, headers=student).status_code == 409


def test_submission_validation_and_attempt_ownership(client, db_session):
    teacher, course, lesson = learning_setup(client, db_session, "submission")
    quiz = generate(client, lesson, teacher).json()
    owner = student_and_enroll(client, course, "owner")
    other = student_and_enroll(client, course, "other")
    attempt = client.post(f"/api/v1/quizzes/{quiz['id']}/attempts", headers=owner).json()
    q1, q2 = quiz["questions"]
    valid1 = {"question_id": q1["id"], "selected_option_id": q1["options"][0]["id"]}
    assert client.post(f"/api/v1/quiz-attempts/{attempt['id']}/submit", json={"answers": [valid1]}, headers=owner).status_code == 422
    assert client.post(f"/api/v1/quiz-attempts/{attempt['id']}/submit", json={"answers": [valid1, valid1]}, headers=owner).status_code == 422
    foreign_option = {"question_id": q1["id"], "selected_option_id": q2["options"][0]["id"]}
    valid2 = {"question_id": q2["id"], "selected_option_id": q2["options"][0]["id"]}
    assert client.post(f"/api/v1/quiz-attempts/{attempt['id']}/submit", json={"answers": [foreign_option, valid2]}, headers=owner).status_code == 422
    other_quiz = generate(client, lesson, teacher).json()
    foreign_question = other_quiz["questions"][0]
    foreign_answer = {"question_id": foreign_question["id"], "selected_option_id": foreign_question["options"][0]["id"]}
    assert client.post(f"/api/v1/quiz-attempts/{attempt['id']}/submit", json={"answers": [foreign_answer, valid2]}, headers=owner).status_code == 422
    assert client.post(f"/api/v1/quiz-attempts/{attempt['id']}/submit", json={"answers": [valid1, valid2]}, headers=other).status_code == 403
    manipulated = {"answers": [valid1, valid2], "correct_count": 2, "score_percent": 100}
    assert client.post(f"/api/v1/quiz-attempts/{attempt['id']}/submit", json=manipulated, headers=owner).status_code == 422
    assert client.get("/api/v1/users/me/quiz-attempts", headers=other).json() == []


@pytest.mark.parametrize(
    "options",
    [
        [{"option_text": str(i), "is_correct": i == 0} for i in range(3)],
        [{"option_text": str(i), "is_correct": i < 2} for i in range(4)],
        [
            {"option_text": "Duplicate", "is_correct": True},
            {"option_text": " duplicate ", "is_correct": False},
            {"option_text": "C", "is_correct": False},
            {"option_text": "D", "is_correct": False},
        ],
    ],
)
def test_generated_question_validation_rejects_bad_options(options):
    with pytest.raises(ValueError):
        GeneratedQuizQuestion.model_validate({"question_text": "Question?", "explanation": "Grounded explanation", "options": options})


def test_completely_correct_and_incorrect_scores(client, db_session):
    teacher, course, lesson = learning_setup(client, db_session, "score-extremes")
    quiz = generate(client, lesson, teacher).json()
    student = student_and_enroll(client, course, "score-extremes")
    for choose_correct, expected in [(True, "100.00"), (False, "0.00")]:
        attempt = client.post(f"/api/v1/quizzes/{quiz['id']}/attempts", headers=student).json()
        answers = []
        for question in quiz["questions"]:
            option = next(o for o in question["options"] if o["is_correct"] is choose_correct)
            answers.append({"question_id": question["id"], "selected_option_id": option["id"]})
        result = client.post(f"/api/v1/quiz-attempts/{attempt['id']}/submit", json={"answers": answers}, headers=student)
        assert result.status_code == 200
        assert result.json()["score_percent"] == expected
