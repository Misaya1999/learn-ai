import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.embedding import get_embedding_service
from app.services.llm import get_answer_generation_service


PASSWORD = "correct-horse-battery-staple"


class RecordingEmbeddingService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def embed_text(self, text: str) -> list[float]:
        self.calls.append(text)
        return [1.0] + [0.0] * 1535


class RecordingAnswerService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate_answer(self, *, instructions: str, input_text: str) -> str:
        self.calls.append(input_text)
        return "A grounded answer."


def auth_headers(client: TestClient, email: str, role: str) -> dict[str, str]:
    registration = client.post(
        "/api/v1/auth/register",
        json={"name": email, "email": email, "password": PASSWORD, "role": role},
    )
    assert registration.status_code == 201
    login = client.post(
        "/api/v1/auth/login", data={"username": email, "password": PASSWORD}
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def learning_setup(client: TestClient) -> tuple[dict, dict, dict[str, str]]:
    owner = auth_headers(client, "material-owner@example.com", "teacher")
    course = client.post(
        "/api/v1/courses", json={"title": "Protected Course"}, headers=owner
    ).json()
    lesson = client.post(
        f"/api/v1/courses/{course['id']}/lessons",
        json={"title": "Protected Lesson", "position": 1},
        headers=owner,
    ).json()
    return course, lesson, owner


def call_endpoint(
    client: TestClient, endpoint: str, lesson_id: str, headers: dict[str, str] | None
):
    path = f"/api/v1/lessons/{lesson_id}/{endpoint}"
    payload = {"query": "What is protected?"} if endpoint == "search" else {
        "question": "What is protected?"
    }
    return client.post(path, json=payload, headers=headers)


@pytest.mark.parametrize("endpoint", ["search", "ask"])
def test_lesson_material_endpoint_requires_authentication(
    client: TestClient, endpoint: str
) -> None:
    _, lesson, _ = learning_setup(client)
    embedding = RecordingEmbeddingService()
    answer = RecordingAnswerService()
    app.dependency_overrides[get_embedding_service] = lambda: embedding
    app.dependency_overrides[get_answer_generation_service] = lambda: answer

    response = call_endpoint(client, endpoint, lesson["id"], None)

    assert response.status_code == 401
    assert embedding.calls == []
    assert answer.calls == []


@pytest.mark.parametrize("endpoint", ["search", "ask"])
@pytest.mark.parametrize(
    ("identity", "role"),
    [("unenrolled-student", "student"), ("non-owner-teacher", "teacher")],
)
def test_lesson_material_endpoint_rejects_unauthorized_users_before_provider_calls(
    client: TestClient, endpoint: str, identity: str, role: str
) -> None:
    _, lesson, _ = learning_setup(client)
    headers = auth_headers(client, f"{identity}@example.com", role)
    embedding = RecordingEmbeddingService()
    answer = RecordingAnswerService()
    app.dependency_overrides[get_embedding_service] = lambda: embedding
    app.dependency_overrides[get_answer_generation_service] = lambda: answer

    response = call_endpoint(client, endpoint, lesson["id"], headers)

    assert response.status_code == 403
    assert embedding.calls == []
    assert answer.calls == []


@pytest.mark.parametrize("endpoint", ["search", "ask"])
@pytest.mark.parametrize("authorized_as", ["owner", "enrolled_student"])
def test_lesson_material_endpoint_allows_authorized_users(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, endpoint: str, authorized_as: str
) -> None:
    course, lesson, owner = learning_setup(client)
    headers = owner
    if authorized_as == "enrolled_student":
        headers = auth_headers(client, "enrolled-material-student@example.com", "student")
        enrollment = client.post(
            f"/api/v1/courses/{course['id']}/enroll", headers=headers
        )
        assert enrollment.status_code == 201

    embedding = RecordingEmbeddingService()
    answer = RecordingAnswerService()
    app.dependency_overrides[get_embedding_service] = lambda: embedding
    app.dependency_overrides[get_answer_generation_service] = lambda: answer
    monkeypatch.setattr("app.api.search.search_lesson_chunks", lambda *args: [])
    monkeypatch.setattr("app.services.tutor.search_lesson_chunks", lambda *args: [])

    response = call_endpoint(client, endpoint, lesson["id"], headers)

    assert response.status_code == 200
    assert len(embedding.calls) == 1
    assert answer.calls == []


@pytest.mark.parametrize("endpoint", ["search", "ask"])
def test_lesson_material_endpoint_returns_authenticated_not_found(
    client: TestClient, endpoint: str
) -> None:
    headers = auth_headers(client, "missing-lesson@example.com", "student")
    embedding = RecordingEmbeddingService()
    answer = RecordingAnswerService()
    app.dependency_overrides[get_embedding_service] = lambda: embedding
    app.dependency_overrides[get_answer_generation_service] = lambda: answer

    response = call_endpoint(client, endpoint, str(uuid.uuid4()), headers)

    assert response.status_code == 404
    assert embedding.calls == []
    assert answer.calls == []
