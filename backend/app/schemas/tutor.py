import uuid

from pydantic import BaseModel, Field, field_validator


class AskQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must not be blank")
        return value


class AnswerSource(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    similarity: float


class AskQuestionResponse(BaseModel):
    answer: str
    sources: list[AnswerSource]
