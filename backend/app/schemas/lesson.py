import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LessonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    content: str | None = None
    position: int = Field(gt=0)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value


class LessonUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    position: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def title_must_be_valid_when_provided(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Title cannot be null")
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value

    @field_validator("position")
    @classmethod
    def position_must_not_be_null(cls, value: int | None) -> int | None:
        if value is None:
            raise ValueError("Position cannot be null")
        return value


class LessonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    content: str | None
    position: int
    created_at: datetime
    updated_at: datetime
