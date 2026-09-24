from io import BytesIO
from pathlib import Path
import uuid

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.main import app
from app.services.embedding import EmbeddingProviderError, get_embedding_service


@pytest.fixture(autouse=True)
def configure_document_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    storage_dir = tmp_path / "documents"
    monkeypatch.setattr(settings, "document_storage_dir", storage_dir)
    monkeypatch.setattr(settings, "document_max_upload_size", 20_000)
    monkeypatch.setattr(settings, "document_chunk_size", 80)
    monkeypatch.setattr(settings, "document_chunk_overlap", 20)
    return storage_dir


def make_pdf(text: str | None) -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output)
    if text is not None:
        text_object = pdf.beginText(72, 750)
        for line in text.splitlines() or [text]:
            text_object.textLine(line)
        pdf.drawText(text_object)
    pdf.showPage()
    pdf.save()
    return output.getvalue()


def create_user_and_headers(
    client: TestClient, email: str, role: str
) -> tuple[dict[str, object], dict[str, str]]:
    password = "correct-horse-battery-staple"
    registered = client.post(
        "/api/v1/auth/register",
        json={"name": role.title(), "email": email, "password": password, "role": role},
    )
    assert registered.status_code == 201
    login = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert login.status_code == 200
    return registered.json(), {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


def create_lesson_for_teacher(
    client: TestClient, headers: dict[str, str]
) -> dict[str, object]:
    course = client.post(
        "/api/v1/courses", json={"title": "Document Course"}, headers=headers
    )
    assert course.status_code == 201
    lesson = client.post(
        f"/api/v1/courses/{course.json()['id']}/lessons",
        json={"title": "Document Lesson", "position": 1},
        headers=headers,
    )
    assert lesson.status_code == 201
    return lesson.json()


def upload_pdf(
    client: TestClient,
    lesson_id: str,
    headers: dict[str, str],
    content: bytes,
    filename: str = "lesson.pdf",
    content_type: str = "application/pdf",
):
    return client.post(
        f"/api/v1/lessons/{lesson_id}/documents",
        files={"file": (filename, content, content_type)},
        headers=headers,
    )


def test_owner_uploads_text_pdf_and_chunks_are_persisted(
    client: TestClient, db_session: Session, configure_document_storage: Path
) -> None:
    teacher, headers = create_user_and_headers(client, "owner@example.com", "teacher")
    lesson = create_lesson_for_teacher(client, headers)
    text = "Deterministic PDF content for LearnAI. " * 12

    response = upload_pdf(client, lesson["id"], headers, make_pdf(text))

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["uploaded_by"] == teacher["id"]
    assert "storage_path" not in body
    document = db_session.get(Document, uuid.UUID(body["id"]))
    assert document is not None
    assert document.status == DocumentStatus.READY
    assert (configure_document_storage / document.storage_path).is_file()
    chunks = list(
        db_session.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        )
    )
    assert len(chunks) > 1
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.embedding is not None for chunk in chunks)
    assert all(len(chunk.embedding) == 1536 for chunk in chunks)


def test_student_and_non_owner_teacher_cannot_upload(client: TestClient) -> None:
    _, owner_headers = create_user_and_headers(client, "owner@example.com", "teacher")
    _, other_headers = create_user_and_headers(client, "other@example.com", "teacher")
    _, student_headers = create_user_and_headers(client, "student@example.com", "student")
    lesson = create_lesson_for_teacher(client, owner_headers)
    pdf = make_pdf("Protected content")

    student = upload_pdf(client, lesson["id"], student_headers, pdf)
    non_owner = upload_pdf(client, lesson["id"], other_headers, pdf)

    assert student.status_code == 403
    assert non_owner.status_code == 403


def test_non_pdf_empty_and_oversized_uploads_are_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, headers = create_user_and_headers(client, "owner@example.com", "teacher")
    lesson = create_lesson_for_teacher(client, headers)

    non_pdf = upload_pdf(
        client, lesson["id"], headers, b"plain text", "notes.txt", "text/plain"
    )
    empty = upload_pdf(client, lesson["id"], headers, b"")
    monkeypatch.setattr(settings, "document_max_upload_size", 10)
    oversized = upload_pdf(client, lesson["id"], headers, make_pdf("too large"))

    assert non_pdf.status_code == 400
    assert empty.status_code == 400
    assert oversized.status_code == 413


def test_pdf_without_extractable_text_is_failed_without_chunks(
    client: TestClient, db_session: Session
) -> None:
    _, headers = create_user_and_headers(client, "owner@example.com", "teacher")
    lesson = create_lesson_for_teacher(client, headers)

    response = upload_pdf(client, lesson["id"], headers, make_pdf(None))

    assert response.status_code == 422
    document = db_session.scalar(select(Document))
    assert document is not None
    assert document.status == DocumentStatus.FAILED
    assert list(db_session.scalars(select(DocumentChunk))) == []


def test_processing_failure_leaves_no_partial_chunks(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, headers = create_user_and_headers(client, "owner@example.com", "teacher")
    lesson = create_lesson_for_teacher(client, headers)

    def fail_chunking(text: str, chunk_size: int, overlap: int) -> list[str]:
        raise ValueError("Safe processing failure")

    monkeypatch.setattr("app.services.document.chunk_text", fail_chunking)
    response = upload_pdf(client, lesson["id"], headers, make_pdf("Valid text"))

    assert response.status_code == 422
    document = db_session.scalar(select(Document))
    assert document is not None
    assert document.status == DocumentStatus.FAILED
    assert db_session.scalar(select(DocumentChunk)) is None


def test_embedding_failure_marks_document_failed_without_chunks(
    client: TestClient, db_session: Session
) -> None:
    _, headers = create_user_and_headers(client, "owner@example.com", "teacher")
    lesson = create_lesson_for_teacher(client, headers)

    class FailingEmbeddingService:
        def embed_texts(self, texts):
            raise EmbeddingProviderError("Provider details must not escape")

        def embed_text(self, text):
            raise EmbeddingProviderError("Provider details must not escape")

    app.dependency_overrides[get_embedding_service] = FailingEmbeddingService
    response = upload_pdf(client, lesson["id"], headers, make_pdf("Valid text"))

    assert response.status_code == 422
    assert response.json()["detail"] == "Embedding generation failed"
    document = db_session.scalar(select(Document))
    assert document is not None
    assert document.status == DocumentStatus.FAILED
    assert db_session.scalar(select(DocumentChunk)) is None


def test_document_listing_and_retrieval(client: TestClient) -> None:
    _, headers = create_user_and_headers(client, "owner@example.com", "teacher")
    lesson = create_lesson_for_teacher(client, headers)
    uploaded = upload_pdf(client, lesson["id"], headers, make_pdf("List this PDF"))
    assert uploaded.status_code == 201

    listing = client.get(f"/api/v1/lessons/{lesson['id']}/documents")
    detail = client.get(f"/api/v1/documents/{uploaded.json()['id']}")

    assert listing.status_code == 200
    assert listing.json() == [uploaded.json()]
    assert detail.status_code == 200
    assert detail.json() == uploaded.json()


def test_only_owner_can_delete_and_deletion_removes_chunks_and_file(
    client: TestClient, db_session: Session, configure_document_storage: Path
) -> None:
    _, owner_headers = create_user_and_headers(client, "owner@example.com", "teacher")
    _, other_headers = create_user_and_headers(client, "other@example.com", "teacher")
    lesson = create_lesson_for_teacher(client, owner_headers)
    uploaded = upload_pdf(
        client,
        lesson["id"],
        owner_headers,
        make_pdf("Delete this document after creating several chunks. " * 10),
    )
    assert uploaded.status_code == 201
    document_id = uuid.UUID(uploaded.json()["id"])
    document = db_session.get(Document, document_id)
    assert document is not None
    stored_path = configure_document_storage / document.storage_path
    assert stored_path.is_file()

    forbidden = client.delete(
        f"/api/v1/documents/{document_id}", headers=other_headers
    )
    deleted = client.delete(
        f"/api/v1/documents/{document_id}", headers=owner_headers
    )

    assert forbidden.status_code == 403
    assert deleted.status_code == 204
    db_session.expire_all()
    assert db_session.get(Document, document_id) is None
    assert db_session.scalar(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    ) is None
    assert not stored_path.exists()
