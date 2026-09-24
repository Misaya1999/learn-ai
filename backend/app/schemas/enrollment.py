import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    enrolled_at: datetime
