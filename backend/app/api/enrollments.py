import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DatabaseSession, StudentUser
from app.schemas.enrollment import EnrollmentRead
from app.services.course import get_course
from app.services.enrollment import (
    AlreadyEnrolledError,
    enroll_student,
    list_student_enrollments,
)

router = APIRouter(tags=["enrollments"])


@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
def enroll(
    course_id: uuid.UUID, db: DatabaseSession, student: StudentUser
) -> EnrollmentRead:
    if get_course(db, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    try:
        return enroll_student(db, student, course_id)
    except AlreadyEnrolledError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this course",
        ) from None


@router.get("/users/me/enrollments", response_model=list[EnrollmentRead])
def read_my_enrollments(
    db: DatabaseSession, student: StudentUser
) -> list[EnrollmentRead]:
    return list_student_enrollments(db, student.id)
