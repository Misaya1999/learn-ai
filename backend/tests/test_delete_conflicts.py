import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.quiz import Quiz
from tests.test_learning import create_course, create_lesson, create_user_and_headers


def add_quiz(db: Session, lesson_id: str, teacher_id: str) -> None:
    db.add(
        Quiz(
            id=uuid.uuid4(),
            lesson_id=uuid.UUID(lesson_id),
            created_by=uuid.UUID(teacher_id),
            title="Protected history",
        )
    )
    db.commit()


def test_owner_deletes_ordinary_lesson(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "delete-owner@example.com", "teacher")
    course = create_course(client, headers)
    lesson = create_lesson(client, course["id"], headers)

    response = client.delete(f"/api/v1/lessons/{lesson['id']}", headers=headers)

    assert response.status_code == 204
    assert client.get(f"/api/v1/lessons/{lesson['id']}").status_code == 404


def test_lesson_with_quiz_returns_conflict_and_session_remains_usable(
    client: TestClient, db_session: Session
) -> None:
    teacher, headers = create_user_and_headers(
        client, "lesson-conflict@example.com", "teacher"
    )
    course = create_course(client, headers)
    lesson = create_lesson(client, course["id"], headers)
    add_quiz(db_session, lesson["id"], teacher["id"])

    response = client.delete(f"/api/v1/lessons/{lesson['id']}", headers=headers)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Lesson cannot be deleted because it has protected learning history"
    }
    assert "constraint" not in response.text.casefold()
    assert client.get(f"/api/v1/lessons/{lesson['id']}").status_code == 200
    follow_up = create_lesson(
        client, course["id"], headers, title="Session still works", position=2
    )
    assert follow_up["title"] == "Session still works"


def test_course_with_quiz_returns_conflict_and_session_remains_usable(
    client: TestClient, db_session: Session
) -> None:
    teacher, headers = create_user_and_headers(
        client, "course-conflict@example.com", "teacher"
    )
    course = create_course(client, headers)
    lesson = create_lesson(client, course["id"], headers)
    add_quiz(db_session, lesson["id"], teacher["id"])

    response = client.delete(f"/api/v1/courses/{course['id']}", headers=headers)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Course cannot be deleted because it has protected learning history"
    }
    assert "constraint" not in response.text.casefold()
    assert client.get(f"/api/v1/courses/{course['id']}").status_code == 200
    assert client.get(f"/api/v1/lessons/{lesson['id']}").status_code == 200


def test_delete_authorization_is_unchanged(client: TestClient) -> None:
    _, owner = create_user_and_headers(client, "delete-auth-owner@example.com", "teacher")
    _, other = create_user_and_headers(client, "delete-auth-other@example.com", "teacher")
    course = create_course(client, owner)
    lesson = create_lesson(client, course["id"], owner)

    assert client.delete(f"/api/v1/lessons/{lesson['id']}", headers=other).status_code == 403
    assert client.delete(f"/api/v1/courses/{course['id']}", headers=other).status_code == 403
