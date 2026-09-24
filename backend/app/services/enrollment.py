import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.models.user import User


class AlreadyEnrolledError(Exception):
    pass


def enroll_student(db: Session, student: User, course_id: uuid.UUID) -> Enrollment:
    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.course_id == course_id,
        )
    )
    if existing is not None:
        raise AlreadyEnrolledError

    enrollment = Enrollment(student_id=student.id, course_id=course_id)
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AlreadyEnrolledError from exc

    db.refresh(enrollment)
    return enrollment


def list_student_enrollments(db: Session, student_id: uuid.UUID) -> list[Enrollment]:
    statement = (
        select(Enrollment)
        .where(Enrollment.student_id == student_id)
        .order_by(Enrollment.enrolled_at, Enrollment.id)
    )
    return list(db.scalars(statement))
