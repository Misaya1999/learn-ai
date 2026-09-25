import uuid

from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import DatabaseSession, OwnedCourse, TeacherUser
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.services import course as course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    course_data: CourseCreate, db: DatabaseSession, teacher: TeacherUser
) -> CourseRead:
    return course_service.create_course(db, course_data, teacher)


@router.get("", response_model=list[CourseRead])
def list_courses(db: DatabaseSession) -> list[CourseRead]:
    return course_service.list_courses(db)


@router.get("/{course_id}", response_model=CourseRead)
def read_course(course_id: uuid.UUID, db: DatabaseSession) -> CourseRead:
    course = course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.patch("/{course_id}", response_model=CourseRead)
def update_course(
    course_data: CourseUpdate, db: DatabaseSession, course: OwnedCourse
) -> CourseRead:
    return course_service.update_course(db, course, course_data)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(db: DatabaseSession, course: OwnedCourse) -> Response:
    try:
        course_service.delete_course(db, course)
    except course_service.CourseDeleteConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course cannot be deleted because it has protected learning history",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
