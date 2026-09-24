import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.api.dependencies import CurrentUser, DatabaseSession, OwnedLesson, StudentUser
from app.core.config import settings
from app.models.quiz import QuizAttempt
from app.models.user import UserRole
from app.schemas.quiz import (
    AttemptHistoryItem, AttemptReview, AttemptReviewItem, AttemptStartRead,
    AttemptSubmitRequest, QuizGenerateRequest, QuizStudentRead, QuizSummary, QuizTeacherRead,
)
from app.services import quiz as quiz_service
from app.services.quiz_generation import (
    QuizGenerationError, QuizGenerationService, QuizGenerationValidationError,
    get_quiz_generation_service,
)

router = APIRouter(tags=["quizzes"])
Generator = Annotated[QuizGenerationService, Depends(get_quiz_generation_service)]


def serialize_quiz(quiz, teacher_view: bool):
    schema = QuizTeacherRead if teacher_view else QuizStudentRead
    return schema.model_validate(quiz).model_dump(mode="json")


def authorize_quiz_read(db, quiz, user):
    if user.role == UserRole.TEACHER:
        if quiz.lesson.course.teacher_id != user.id:
            raise HTTPException(status_code=403, detail="You do not own this course")
        return True
    if user.role == UserRole.STUDENT:
        try:
            quiz_service.require_enrollment(db, user.id, quiz)
        except quiz_service.NotEnrolledError:
            raise HTTPException(status_code=403, detail="Enrollment required") from None
        return False
    raise HTTPException(status_code=403, detail="Access forbidden")


@router.post("/lessons/{lesson_id}/quizzes/generate", status_code=status.HTTP_201_CREATED)
def generate_quiz(request: QuizGenerateRequest, db: DatabaseSession, lesson: OwnedLesson, teacher: CurrentUser, generator: Generator):
    try:
        quiz = quiz_service.generate_quiz(db, lesson, teacher, request, generator, settings.quiz_generation_max_context_characters)
    except quiz_service.NoQuizMaterialError:
        raise HTTPException(status_code=422, detail="No usable ready lesson material") from None
    except QuizGenerationValidationError:
        raise HTTPException(status_code=502, detail="Quiz provider returned invalid output") from None
    except QuizGenerationError:
        raise HTTPException(status_code=502, detail="Unable to generate quiz") from None
    return serialize_quiz(quiz, True)


@router.get("/lessons/{lesson_id}/quizzes", response_model=list[QuizSummary])
def list_quizzes(lesson_id: uuid.UUID, db: DatabaseSession, current_user: CurrentUser):
    from app.services.lesson import get_lesson
    lesson = get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    quizzes = quiz_service.list_lesson_quizzes(db, lesson_id)
    if current_user.role == UserRole.TEACHER:
        if lesson.course.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not own this course")
    elif current_user.role == UserRole.STUDENT and not quiz_service.student_is_enrolled(db, current_user.id, lesson.course_id):
        raise HTTPException(status_code=403, detail="Enrollment required")
    return quizzes


@router.get("/quizzes/{quiz_id}")
def read_quiz(quiz_id: uuid.UUID, db: DatabaseSession, current_user: CurrentUser):
    quiz = quiz_service.get_quiz(db, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    teacher_view = authorize_quiz_read(db, quiz, current_user)
    return serialize_quiz(quiz, teacher_view)


@router.post("/quizzes/{quiz_id}/attempts", status_code=status.HTTP_201_CREATED)
def start_quiz_attempt(quiz_id: uuid.UUID, db: DatabaseSession, student: StudentUser):
    quiz = quiz_service.get_quiz(db, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    try:
        attempt = quiz_service.start_attempt(db, quiz, student)
    except quiz_service.NotEnrolledError:
        raise HTTPException(status_code=403, detail="Enrollment required") from None
    return AttemptStartRead(id=attempt.id, quiz=QuizStudentRead.model_validate(quiz), total_questions=attempt.total_questions, started_at=attempt.started_at)


@router.post("/quiz-attempts/{attempt_id}/submit", response_model=AttemptReview)
def submit_quiz_attempt(attempt_id: uuid.UUID, request: AttemptSubmitRequest, db: DatabaseSession, student: StudentUser):
    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    if attempt.student_id != student.id:
        raise HTTPException(status_code=403, detail="You do not own this attempt")
    try:
        attempt, review = quiz_service.submit_attempt(db, attempt, request)
    except quiz_service.AttemptAlreadySubmittedError:
        raise HTTPException(status_code=409, detail="Quiz attempt already submitted") from None
    except quiz_service.InvalidAttemptSubmissionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return AttemptReview(
        attempt_id=attempt.id, quiz_id=attempt.quiz_id, correct_count=attempt.correct_count,
        total_questions=attempt.total_questions, score_percent=attempt.score_percent, submitted_at=attempt.submitted_at,
        answers=[AttemptReviewItem(
            question_id=q.id, question_text=q.question_text,
            selected_option_id=selected.id, selected_option_text=selected.option_text,
            correct_option_id=correct.id, correct_option_text=correct.option_text,
            is_correct=is_correct, explanation=q.explanation,
        ) for q, selected, correct, is_correct in review],
    )


@router.get("/users/me/quiz-attempts", response_model=list[AttemptHistoryItem])
def my_quiz_attempts(db: DatabaseSession, student: StudentUser):
    return [AttemptHistoryItem(
        attempt_id=attempt.id, quiz_id=attempt.quiz_id, quiz_title=attempt.quiz.title,
        lesson_id=attempt.quiz.lesson_id, lesson_title=attempt.quiz.lesson.title,
        correct_count=attempt.correct_count, total_questions=attempt.total_questions,
        score_percent=attempt.score_percent, started_at=attempt.started_at, submitted_at=attempt.submitted_at,
    ) for attempt in quiz_service.list_student_attempts(db, student.id)]
