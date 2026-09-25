import uuid

import pytest
from fastapi.testclient import TestClient

from app.services.search import SearchMatch


def create_lesson(client: TestClient) -> tuple[dict[str, object], dict[str, str]]:
    password = "correct-horse-battery-staple"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Search Teacher",
            "email": "search@example.com",
            "password": password,
            "role": "teacher",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "search@example.com", "password": password},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    course = client.post(
        "/api/v1/courses", json={"title": "Search Course"}, headers=headers
    )
    lesson = client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Search Lesson", "position": 1},
        headers=headers,
    )
    assert registration.status_code == 201
    assert lesson.status_code == 201
    return lesson.json(), headers


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "x" * 2001},
        {"query": "valid", "limit": 0},
        {"query": "valid", "limit": 21},
    ],
)
def test_semantic_search_validates_query_and_limit(
    client: TestClient, payload: dict[str, object]
) -> None:
    lesson, headers = create_lesson(client)
    response = client.post(
        f"/api/v1/lessons/{lesson['id']}/search", json=payload, headers=headers
    )

    assert response.status_code == 422


def test_semantic_search_response_exposes_only_retrieval_metadata(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    lesson, headers = create_lesson(client)
    document_id = uuid.uuid4()

    def fake_search(db, lesson_id, query_embedding, limit):
        assert str(lesson_id) == lesson["id"]
        assert len(query_embedding) == 1536
        assert limit == 3
        return [
            SearchMatch(
                document_id=document_id,
                original_filename="knowledge.pdf",
                chunk_index=0,
                content="Relevant content",
                similarity=0.875,
            )
        ]

    monkeypatch.setattr("app.api.search.search_lesson_chunks", fake_search)
    response = client.post(
        f"/api/v1/lessons/{lesson['id']}/search",
        json={"query": "supervised learning", "limit": 3},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "document_id": str(document_id),
            "original_filename": "knowledge.pdf",
            "chunk_index": 0,
            "content": "Relevant content",
            "similarity": 0.875,
        }
    ]
    assert "embedding" not in response.text
    assert "storage_path" not in response.text
