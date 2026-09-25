import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate


class CourseDeleteConflictError(Exception):
    pass


def create_course(db: Session, course_data: CourseCreate, teacher: User) -> Course:
    course = Course(teacher_id=teacher.id, **course_data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def list_courses(db: Session) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.created_at, Course.id)))


def get_course(db: Session, course_id: uuid.UUID) -> Course | None:
    return db.get(Course, course_id)


def update_course(db: Session, course: Course, course_data: CourseUpdate) -> Course:
    for field, value in course_data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CourseDeleteConflictError from exc
