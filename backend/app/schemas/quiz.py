import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GeneratedQuizOption(BaseModel):
    option_text: str = Field(min_length=1, max_length=1000)
    is_correct: bool

    @field_validator("option_text")
    @classmethod
    def strip_option(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Option must not be blank")
        return value


class GeneratedQuizQuestion(BaseModel):
    question_text: str = Field(min_length=1, max_length=2000)
    options: list[GeneratedQuizOption] = Field(min_length=4, max_length=4)
    explanation: str = Field(min_length=1, max_length=4000)

    @field_validator("question_text", "explanation")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Text must not be blank")
        return value

    @model_validator(mode="after")
    def validate_options(self):
        if sum(option.is_correct for option in self.options) != 1:
            raise ValueError("Each question must have exactly one correct option")
        normalized = [" ".join(option.option_text.casefold().split()) for option in self.options]
        if len(set(normalized)) != len(normalized):
            raise ValueError("Options must be unique within a question")
        return self


class GeneratedQuiz(BaseModel):
    questions: list[GeneratedQuizQuestion]


class QuizGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    question_count: int = Field(ge=1, le=10)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title must not be blank")
        return value


class QuizOptionStudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    option_text: str
    position: int


class QuizOptionTeacherRead(QuizOptionStudentRead):
    is_correct: bool


class QuizQuestionStudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    question_text: str
    position: int
    options: list[QuizOptionStudentRead]


class QuizQuestionTeacherRead(QuizQuestionStudentRead):
    explanation: str
    options: list[QuizOptionTeacherRead]


class QuizStudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    questions: list[QuizQuestionStudentRead]


class QuizTeacherRead(QuizStudentRead):
    created_by: uuid.UUID
    created_at: datetime
    questions: list[QuizQuestionTeacherRead]


class QuizSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    created_at: datetime


class AttemptStartRead(BaseModel):
    id: uuid.UUID
    quiz: QuizStudentRead
    total_questions: int
    started_at: datetime


class AttemptAnswerSubmit(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID


class AttemptSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[AttemptAnswerSubmit]

    @model_validator(mode="after")
    def reject_duplicate_questions(self):
        ids = [answer.question_id for answer in self.answers]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate question IDs are not allowed")
        return self


class AttemptReviewItem(BaseModel):
    question_id: uuid.UUID
    question_text: str
    selected_option_id: uuid.UUID
    selected_option_text: str
    correct_option_id: uuid.UUID
    correct_option_text: str
    is_correct: bool
    explanation: str


class AttemptReview(BaseModel):
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    correct_count: int
    total_questions: int
    score_percent: Decimal
    submitted_at: datetime
    answers: list[AttemptReviewItem]


class AttemptHistoryItem(BaseModel):
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    lesson_id: uuid.UUID
    lesson_title: str
    correct_count: int | None
    total_questions: int
    score_percent: Decimal | None
    started_at: datetime
    submitted_at: datetime | None
