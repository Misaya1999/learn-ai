import uuid
from pathlib import PurePath

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.lesson import Lesson
from app.models.user import User
from app.services.chunking import chunk_text
from app.services.embedding import EmbeddingService, EmbeddingServiceError
from app.services.pdf import NoExtractableTextError, PDFExtractionError, extract_pdf_text
from app.services.storage import (
    EmptyUploadError,
    LocalDocumentStorage,
    UploadTooLargeError,
)


class InvalidDocumentUploadError(ValueError):
    pass


class DocumentProcessingError(ValueError):
    pass


def validate_pdf_upload(upload: UploadFile) -> str:
    if not upload.filename:
        raise InvalidDocumentUploadError("A filename is required")
    filename = PurePath(upload.filename.replace("\\", "/")).name
    if not filename or filename in {".", ".."}:
        raise InvalidDocumentUploadError("A filename is required")
    if len(filename) > 255:
        raise InvalidDocumentUploadError("Filename is too long")
    if PurePath(filename).suffix.casefold() != ".pdf":
        raise InvalidDocumentUploadError("Only .pdf files are accepted")
    if (upload.content_type or "").casefold() != "application/pdf":
        raise InvalidDocumentUploadError("File content type must be application/pdf")
    return filename


def process_document_upload(
    db: Session,
    lesson: Lesson,
    uploader: User,
    upload: UploadFile,
    storage: LocalDocumentStorage,
    embedding_service: EmbeddingService,
) -> Document:
    original_filename = validate_pdf_upload(upload)
    stored = storage.save(upload)
    document = Document(
        lesson_id=lesson.id,
        uploaded_by=uploader.id,
        original_filename=original_filename,
        content_type="application/pdf",
        file_size=stored.size,
        storage_path=stored.key,
        status=DocumentStatus.PROCESSING,
    )
    db.add(document)
    try:
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        storage.delete(stored.key)
        raise

    try:
        text = extract_pdf_text(stored.path)
        chunks = chunk_text(
            text,
            chunk_size=settings.document_chunk_size,
            overlap=settings.document_chunk_overlap,
        )
        if not chunks:
            raise NoExtractableTextError("PDF contains no extractable text")
        try:
            embeddings = embedding_service.embed_texts(chunks)
        except EmbeddingServiceError as exc:
            raise DocumentProcessingError("Embedding generation failed") from exc
        if len(embeddings) != len(chunks):
            raise DocumentProcessingError("Embedding generation failed")
        db.add_all(
            DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=content,
                embedding=embedding,
            )
            for index, (content, embedding) in enumerate(
                zip(chunks, embeddings, strict=True)
            )
        )
        document.status = DocumentStatus.READY
        db.commit()
        db.refresh(document)
        return document
    except (PDFExtractionError, ValueError) as exc:
        db.rollback()
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        document.status = DocumentStatus.FAILED
        db.commit()
        raise DocumentProcessingError(str(exc)) from exc
    except Exception as exc:
        db.rollback()
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        document.status = DocumentStatus.FAILED
        db.commit()
        raise DocumentProcessingError("Document processing failed") from exc


def list_lesson_documents(db: Session, lesson_id: uuid.UUID) -> list[Document]:
    statement = (
        select(Document)
        .where(Document.lesson_id == lesson_id)
        .order_by(Document.created_at, Document.id)
    )
    return list(db.scalars(statement))


def get_document(db: Session, document_id: uuid.UUID) -> Document | None:
    return db.get(Document, document_id)


def delete_document(
    db: Session, document: Document, storage: LocalDocumentStorage
) -> None:
    storage.delete(document.storage_path)
    db.delete(document)
    db.commit()


__all__ = [
    "DocumentProcessingError",
    "EmptyUploadError",
    "InvalidDocumentUploadError",
    "UploadTooLargeError",
    "delete_document",
    "get_document",
    "list_lesson_documents",
    "process_document_upload",
]
