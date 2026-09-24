import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.api.dependencies import DatabaseSession, OwnedDocument, OwnedLesson, TeacherUser
from app.schemas.document import DocumentRead
from app.services.course import get_course
from app.services.document import (
    DocumentProcessingError,
    EmptyUploadError,
    InvalidDocumentUploadError,
    UploadTooLargeError,
    delete_document,
    get_document,
    list_lesson_documents,
    process_document_upload,
)
from app.services.embedding import EmbeddingService, get_embedding_service
from app.services.lesson import get_lesson
from app.services.storage import LocalDocumentStorage, get_document_storage

router = APIRouter(tags=["documents"])
DocumentStorage = Annotated[LocalDocumentStorage, Depends(get_document_storage)]
DocumentEmbeddingService = Annotated[EmbeddingService, Depends(get_embedding_service)]


@router.post(
    "/lessons/{lesson_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: Annotated[UploadFile, File()],
    db: DatabaseSession,
    lesson: OwnedLesson,
    teacher: TeacherUser,
    storage: DocumentStorage,
    embedding_service: DocumentEmbeddingService,
) -> DocumentRead:
    try:
        return process_document_upload(
            db, lesson, teacher, file, storage, embedding_service
        )
    except InvalidDocumentUploadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    except EmptyUploadError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty"
        ) from None
    except UploadTooLargeError:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file exceeds the configured size limit",
        ) from None
    except DocumentProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from None


@router.get(
    "/lessons/{lesson_id}/documents", response_model=list[DocumentRead]
)
def list_documents(lesson_id: uuid.UUID, db: DatabaseSession) -> list[DocumentRead]:
    lesson = get_lesson(db, lesson_id)
    if lesson is None or get_course(db, lesson.course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return list_lesson_documents(db, lesson_id)


@router.get("/documents/{document_id}", response_model=DocumentRead)
def read_document(document_id: uuid.UUID, db: DatabaseSession) -> DocumentRead:
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(
    db: DatabaseSession, document: OwnedDocument, storage: DocumentStorage
) -> Response:
    delete_document(db, document, storage)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
