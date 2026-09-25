import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonUpdate


class LessonDeleteConflictError(Exception):
    pass


def create_lesson(db: Session, course: Course, lesson_data: LessonCreate) -> Lesson:
    lesson = Lesson(course_id=course.id, **lesson_data.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def list_course_lessons(db: Session, course_id: uuid.UUID) -> list[Lesson]:
    statement = (
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.position, Lesson.created_at, Lesson.id)
    )
    return list(db.scalars(statement))


def get_lesson(db: Session, lesson_id: uuid.UUID) -> Lesson | None:
    return db.get(Lesson, lesson_id)


def update_lesson(db: Session, lesson: Lesson, lesson_data: LessonUpdate) -> Lesson:
    for field, value in lesson_data.model_dump(exclude_unset=True).items():
        setattr(lesson, field, value)
    db.commit()
    db.refresh(lesson)
    return lesson


def delete_lesson(db: Session, lesson: Lesson) -> None:
    db.delete(lesson)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise LessonDeleteConflictError from exc
