import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value


class CourseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_be_valid_when_provided(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Title cannot be null")
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    teacher_id: uuid.UUID
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
