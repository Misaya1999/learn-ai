import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    uploaded_by: uuid.UUID
    original_filename: str
    content_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
