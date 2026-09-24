"""Add quizzes, attempts, and deterministic grading records.

Revision ID: 20260924_05
Revises: 20260924_04
Create Date: 2026-09-24
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260924_05"
down_revision: str | None = "20260924_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("quizzes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_quizzes_lesson_id", "quizzes", ["lesson_id"])
    op.create_index("ix_quizzes_created_by", "quizzes", ["created_by"])
    op.create_table("quiz_questions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("quiz_id", sa.Uuid(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False), sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("position > 0", name="ck_quiz_questions_position_positive"),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quiz_id", "position", name="uq_quiz_questions_quiz_position"))
    op.create_index("ix_quiz_questions_quiz_id", "quiz_questions", ["quiz_id"])
    op.create_table("quiz_options",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False), sa.Column("is_correct", sa.Boolean(), nullable=False), sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position > 0", name="ck_quiz_options_position_positive"),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_questions.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "position", name="uq_quiz_options_question_position"))
    op.create_index("ix_quiz_options_question_id", "quiz_options", ["question_id"])
    op.create_table("quiz_attempts",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("quiz_id", sa.Uuid(), nullable=False), sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=True), sa.Column("total_questions", sa.Integer(), nullable=False), sa.Column("score_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("total_questions > 0", name="ck_quiz_attempts_total_positive"),
        sa.CheckConstraint("correct_count IS NULL OR (correct_count >= 0 AND correct_count <= total_questions)", name="ck_quiz_attempts_correct_range"),
        sa.CheckConstraint("score_percent IS NULL OR (score_percent >= 0 AND score_percent <= 100)", name="ck_quiz_attempts_score_range"),
        sa.CheckConstraint("(submitted_at IS NULL AND correct_count IS NULL AND score_percent IS NULL) OR (submitted_at IS NOT NULL AND correct_count IS NOT NULL AND score_percent IS NOT NULL)", name="ck_quiz_attempts_submission_state"),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_quiz_attempts_quiz_id", "quiz_attempts", ["quiz_id"])
    op.create_index("ix_quiz_attempts_student_id", "quiz_attempts", ["student_id"])
    op.create_table("quiz_attempt_answers",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("attempt_id", sa.Uuid(), nullable=False), sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("selected_option_id", sa.Uuid(), nullable=False), sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["quiz_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_questions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["selected_option_id"], ["quiz_options.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_quiz_attempt_answers_attempt_question"))
    op.create_index("ix_quiz_attempt_answers_attempt_id", "quiz_attempt_answers", ["attempt_id"])
    op.create_index("ix_quiz_attempt_answers_question_id", "quiz_attempt_answers", ["question_id"])
    op.create_index("ix_quiz_attempt_answers_selected_option_id", "quiz_attempt_answers", ["selected_option_id"])


def downgrade() -> None:
    op.drop_table("quiz_attempt_answers")
    op.drop_table("quiz_attempts")
    op.drop_table("quiz_options")
    op.drop_table("quiz_questions")
    op.drop_table("quizzes")
