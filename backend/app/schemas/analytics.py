import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class StudentAnalyticsOverview(BaseModel):
    total_submitted_attempts: int
    distinct_quizzes_attempted: int
    distinct_lessons_practiced: int
    average_score: Decimal | None
    best_score: Decimal | None
    total_questions_answered: int
    total_correct_answers: int
    overall_accuracy_percent: Decimal | None


class StudentLessonAnalytics(BaseModel):
    lesson_id: uuid.UUID
    lesson_title: str
    submitted_attempts: int
    average_score: Decimal
    best_score: Decimal
    total_questions: int
    correct_answers: int
    accuracy_percent: Decimal


class StudentProgressPoint(BaseModel):
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    lesson_id: uuid.UUID
    lesson_title: str
    score_percent: Decimal
    submitted_at: datetime


class CourseAnalyticsOverview(BaseModel):
    course_id: uuid.UUID
    enrolled_students: int
    students_with_submitted_attempts: int
    total_submitted_attempts: int
    average_score: Decimal | None
    total_questions_answered: int
    total_correct_answers: int
    overall_accuracy_percent: Decimal | None


class CourseStudentAnalytics(BaseModel):
    student_id: uuid.UUID
    student_name: str
    submitted_attempts: int
    average_score: Decimal | None
    best_score: Decimal | None
    total_questions: int
    correct_answers: int
    accuracy_percent: Decimal | None


class CourseLessonAnalytics(BaseModel):
    lesson_id: uuid.UUID
    lesson_title: str
    quizzes: int
    submitted_attempts: int
    participating_students: int
    average_score: Decimal | None
    total_questions: int
    correct_answers: int
    accuracy_percent: Decimal | None


class CourseQuestionAnalytics(BaseModel):
    question_id: uuid.UUID
    quiz_id: uuid.UUID
    question_text: str
    lesson_id: uuid.UUID
    total_answers: int
    correct_answers: int
    incorrect_answers: int
    accuracy_percent: Decimal | None
