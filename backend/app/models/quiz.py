from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lesson import Lesson
    from app.models.user import User


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id", ondelete="RESTRICT"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lesson: Mapped["Lesson"] = relationship(back_populates="quizzes")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="quiz", cascade="all, delete-orphan", passive_deletes=True, order_by="QuizQuestion.position")
    attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="quiz")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    __table_args__ = (
        CheckConstraint("position > 0", name="ck_quiz_questions_position_positive"),
        UniqueConstraint("quiz_id", "position", name="uq_quiz_questions_quiz_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    quiz: Mapped[Quiz] = relationship(back_populates="questions")
    options: Mapped[list["QuizOption"]] = relationship(back_populates="question", cascade="all, delete-orphan", passive_deletes=True, order_by="QuizOption.position")


class QuizOption(Base):
    __tablename__ = "quiz_options"
    __table_args__ = (
        CheckConstraint("position > 0", name="ck_quiz_options_position_positive"),
        UniqueConstraint("question_id", "position", name="uq_quiz_options_question_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"), index=True)
    option_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    position: Mapped[int] = mapped_column(Integer)

    question: Mapped[QuizQuestion] = relationship(back_populates="options")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        CheckConstraint("total_questions > 0", name="ck_quiz_attempts_total_positive"),
        CheckConstraint("correct_count IS NULL OR (correct_count >= 0 AND correct_count <= total_questions)", name="ck_quiz_attempts_correct_range"),
        CheckConstraint("score_percent IS NULL OR (score_percent >= 0 AND score_percent <= 100)", name="ck_quiz_attempts_score_range"),
        CheckConstraint("(submitted_at IS NULL AND correct_count IS NULL AND score_percent IS NULL) OR (submitted_at IS NOT NULL AND correct_count IS NOT NULL AND score_percent IS NOT NULL)", name="ck_quiz_attempts_submission_state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="RESTRICT"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer)
    score_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quiz: Mapped[Quiz] = relationship(back_populates="attempts")
    student: Mapped["User"] = relationship(foreign_keys=[student_id])
    answers: Mapped[list["QuizAttemptAnswer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan", passive_deletes=True)


class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_quiz_attempt_answers_attempt_question"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quiz_questions.id", ondelete="RESTRICT"), index=True)
    selected_option_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quiz_options.id", ondelete="RESTRICT"), index=True)
    is_correct: Mapped[bool] = mapped_column(Boolean)

    attempt: Mapped[QuizAttempt] = relationship(back_populates="answers")
    question: Mapped[QuizQuestion] = relationship()
    selected_option: Mapped[QuizOption] = relationship()
