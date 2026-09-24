import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import ROOT_DIR, settings


class EmptyUploadError(ValueError):
    pass


class UploadTooLargeError(ValueError):
    pass


class UnsafeStorageKeyError(ValueError):
    pass


@dataclass(frozen=True)
class StoredFile:
    key: str
    size: int
    path: Path


class LocalDocumentStorage:
    def __init__(self, root: Path, max_upload_size: int) -> None:
        self.root = root if root.is_absolute() else ROOT_DIR / root
        self.max_upload_size = max_upload_size

    def save(self, upload: UploadFile) -> StoredFile:
        self.root.mkdir(parents=True, exist_ok=True)
        key = f"{uuid.uuid4().hex}.pdf"
        target = self._resolve(key)
        size = 0

        try:
            with target.open("xb") as output:
                while data := upload.file.read(64 * 1024):
                    size += len(data)
                    if size > self.max_upload_size:
                        raise UploadTooLargeError
                    output.write(data)
            if size == 0:
                raise EmptyUploadError
        except Exception:
            target.unlink(missing_ok=True)
            raise

        return StoredFile(key=key, size=size, path=target)

    def path_for(self, key: str) -> Path:
        return self._resolve(key)

    def delete(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def _resolve(self, key: str) -> Path:
        if not key or Path(key).name != key:
            raise UnsafeStorageKeyError("Invalid storage key")
        root = self.root.resolve()
        candidate = (root / key).resolve()
        if candidate.parent != root:
            raise UnsafeStorageKeyError("Invalid storage key")
        return candidate


def get_document_storage() -> LocalDocumentStorage:
    return LocalDocumentStorage(
        root=settings.document_storage_dir,
        max_upload_size=settings.document_max_upload_size,
    )
