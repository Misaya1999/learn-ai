import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.quiz import Quiz, QuizAttempt, QuizAttemptAnswer, QuizQuestion
from app.models.user import User
from app.schemas.analytics import (
    CourseAnalyticsOverview, CourseLessonAnalytics, CourseQuestionAnalytics,
    CourseStudentAnalytics, StudentAnalyticsOverview, StudentLessonAnalytics,
    StudentProgressPoint,
)

TWO_PLACES = Decimal("0.01")


def decimal_or_none(value) -> Decimal | None:
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP) if value is not None else None


def accuracy(correct: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(correct) * 100 / Decimal(total)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def average_score(score_sum, count: int) -> Decimal | None:
    if count == 0:
        return None
    return (Decimal(str(score_sum)) / Decimal(count)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def student_overview(db: Session, student_id: uuid.UUID) -> StudentAnalyticsOverview:
    row = db.execute(
        select(
            func.count(QuizAttempt.id), func.count(distinct(QuizAttempt.quiz_id)),
            func.count(distinct(Quiz.lesson_id)), func.sum(QuizAttempt.score_percent),
            func.max(QuizAttempt.score_percent), func.coalesce(func.sum(QuizAttempt.total_questions), 0),
            func.coalesce(func.sum(QuizAttempt.correct_count), 0),
        ).join(Quiz, Quiz.id == QuizAttempt.quiz_id).where(
            QuizAttempt.student_id == student_id, QuizAttempt.submitted_at.is_not(None)
        )
    ).one()
    total, quizzes, lessons, score_sum, best, questions, correct = row
    return StudentAnalyticsOverview(
        total_submitted_attempts=total, distinct_quizzes_attempted=quizzes,
        distinct_lessons_practiced=lessons, average_score=average_score(score_sum, total),
        best_score=decimal_or_none(best), total_questions_answered=questions,
        total_correct_answers=correct, overall_accuracy_percent=accuracy(correct, questions),
    )


def student_lessons(db: Session, student_id: uuid.UUID) -> list[StudentLessonAnalytics]:
    rows = db.execute(
        select(Lesson.id, Lesson.title, func.count(QuizAttempt.id), func.sum(QuizAttempt.score_percent),
               func.max(QuizAttempt.score_percent), func.sum(QuizAttempt.total_questions), func.sum(QuizAttempt.correct_count))
        .join(Quiz, Quiz.lesson_id == Lesson.id).join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(QuizAttempt.student_id == student_id, QuizAttempt.submitted_at.is_not(None))
        .group_by(Lesson.id, Lesson.title).order_by(Lesson.position, Lesson.created_at, Lesson.id)
    ).all()
    return [StudentLessonAnalytics(
        lesson_id=r[0], lesson_title=r[1], submitted_attempts=r[2], average_score=average_score(r[3], r[2]),
        best_score=decimal_or_none(r[4]), total_questions=r[5], correct_answers=r[6], accuracy_percent=accuracy(r[6], r[5])
    ) for r in rows]


def student_progress(db: Session, student_id: uuid.UUID) -> list[StudentProgressPoint]:
    rows = db.execute(
        select(QuizAttempt.id, Quiz.id, Quiz.title, Lesson.id, Lesson.title, QuizAttempt.score_percent, QuizAttempt.submitted_at)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id).join(Lesson, Lesson.id == Quiz.lesson_id)
        .where(QuizAttempt.student_id == student_id, QuizAttempt.submitted_at.is_not(None))
        .order_by(QuizAttempt.submitted_at, QuizAttempt.id)
    ).all()
    return [StudentProgressPoint(attempt_id=r[0], quiz_id=r[1], quiz_title=r[2], lesson_id=r[3], lesson_title=r[4], score_percent=decimal_or_none(r[5]), submitted_at=r[6]) for r in rows]


def course_overview(db: Session, course_id: uuid.UUID) -> CourseAnalyticsOverview:
    enrolled = db.scalar(select(func.count(Enrollment.id)).where(Enrollment.course_id == course_id)) or 0
    row = db.execute(
        select(func.count(QuizAttempt.id), func.count(distinct(QuizAttempt.student_id)), func.sum(QuizAttempt.score_percent),
               func.coalesce(func.sum(QuizAttempt.total_questions), 0), func.coalesce(func.sum(QuizAttempt.correct_count), 0))
        .select_from(QuizAttempt).join(Quiz, Quiz.id == QuizAttempt.quiz_id).join(Lesson, Lesson.id == Quiz.lesson_id)
        .where(Lesson.course_id == course_id, QuizAttempt.submitted_at.is_not(None))
    ).one()
    attempts, students, score_sum, questions, correct = row
    return CourseAnalyticsOverview(course_id=course_id, enrolled_students=enrolled,
        students_with_submitted_attempts=students, total_submitted_attempts=attempts,
        average_score=average_score(score_sum, attempts), total_questions_answered=questions,
        total_correct_answers=correct, overall_accuracy_percent=accuracy(correct, questions))


def course_students(db: Session, course_id: uuid.UUID) -> list[CourseStudentAnalytics]:
    aggregates = (
        select(QuizAttempt.student_id.label("student_id"), func.count(QuizAttempt.id).label("attempts"),
               func.sum(QuizAttempt.score_percent).label("score_sum"), func.max(QuizAttempt.score_percent).label("best"),
               func.sum(QuizAttempt.total_questions).label("questions"), func.sum(QuizAttempt.correct_count).label("correct"))
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id).join(Lesson, Lesson.id == Quiz.lesson_id)
        .where(Lesson.course_id == course_id, QuizAttempt.submitted_at.is_not(None)).group_by(QuizAttempt.student_id).subquery()
    )
    rows = db.execute(
        select(User.id, User.name, aggregates.c.attempts, aggregates.c.score_sum, aggregates.c.best, aggregates.c.questions, aggregates.c.correct)
        .join(Enrollment, Enrollment.student_id == User.id)
        .outerjoin(aggregates, aggregates.c.student_id == User.id)
        .where(Enrollment.course_id == course_id).order_by(User.name, User.id)
    ).all()
    result = []
    for r in rows:
        attempts, questions, correct = r[2] or 0, r[5] or 0, r[6] or 0
        result.append(CourseStudentAnalytics(student_id=r[0], student_name=r[1], submitted_attempts=attempts,
            average_score=average_score(r[3], attempts), best_score=decimal_or_none(r[4]), total_questions=questions,
            correct_answers=correct, accuracy_percent=accuracy(correct, questions)))
    return result


def course_lessons(db: Session, course_id: uuid.UUID) -> list[CourseLessonAnalytics]:
    quiz_counts = select(Quiz.lesson_id.label("lesson_id"), func.count(Quiz.id).label("quizzes")).group_by(Quiz.lesson_id).subquery()
    attempt_stats = (
        select(Quiz.lesson_id.label("lesson_id"), func.count(QuizAttempt.id).label("attempts"),
               func.count(distinct(QuizAttempt.student_id)).label("students"), func.sum(QuizAttempt.score_percent).label("score_sum"),
               func.sum(QuizAttempt.total_questions).label("questions"), func.sum(QuizAttempt.correct_count).label("correct"))
        .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(QuizAttempt.submitted_at.is_not(None)).group_by(Quiz.lesson_id).subquery()
    )
    rows = db.execute(
        select(Lesson.id, Lesson.title, quiz_counts.c.quizzes, attempt_stats.c.attempts, attempt_stats.c.students,
               attempt_stats.c.score_sum, attempt_stats.c.questions, attempt_stats.c.correct)
        .outerjoin(quiz_counts, quiz_counts.c.lesson_id == Lesson.id).outerjoin(attempt_stats, attempt_stats.c.lesson_id == Lesson.id)
        .where(Lesson.course_id == course_id).order_by(Lesson.position, Lesson.created_at, Lesson.id)
    ).all()
    return [CourseLessonAnalytics(lesson_id=r[0], lesson_title=r[1], quizzes=r[2] or 0, submitted_attempts=r[3] or 0,
        participating_students=r[4] or 0, average_score=average_score(r[5], r[3] or 0), total_questions=r[6] or 0,
        correct_answers=r[7] or 0, accuracy_percent=accuracy(r[7] or 0, r[6] or 0)) for r in rows]


def course_questions(db: Session, course_id: uuid.UUID) -> list[CourseQuestionAnalytics]:
    answer_stats = (
        select(QuizAttemptAnswer.question_id.label("question_id"), func.count(QuizAttemptAnswer.id).label("total"),
               func.sum(case((QuizAttemptAnswer.is_correct.is_(True), 1), else_=0)).label("correct"))
        .join(QuizAttempt, QuizAttempt.id == QuizAttemptAnswer.attempt_id)
        .where(QuizAttempt.submitted_at.is_not(None)).group_by(QuizAttemptAnswer.question_id).subquery()
    )
    rows = db.execute(
        select(QuizQuestion.id, Quiz.id, QuizQuestion.question_text, Lesson.id, answer_stats.c.total, answer_stats.c.correct)
        .join(Quiz, Quiz.id == QuizQuestion.quiz_id).join(Lesson, Lesson.id == Quiz.lesson_id)
        .outerjoin(answer_stats, answer_stats.c.question_id == QuizQuestion.id)
        .where(Lesson.course_id == course_id).order_by(Lesson.position, Quiz.created_at, Quiz.id, QuizQuestion.position, QuizQuestion.id)
    ).all()
    result = []
    for r in rows:
        total, correct = r[4] or 0, r[5] or 0
        result.append(CourseQuestionAnalytics(question_id=r[0], quiz_id=r[1], question_text=r[2], lesson_id=r[3],
            total_answers=total, correct_answers=correct, incorrect_answers=total-correct, accuracy_percent=accuracy(correct, total)))
    return result
