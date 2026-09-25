import uuid

from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import DatabaseSession, OwnedCourse, OwnedLesson
from app.schemas.lesson import LessonCreate, LessonRead, LessonUpdate
from app.services import lesson as lesson_service
from app.services.course import get_course

router = APIRouter(tags=["lessons"])


@router.post(
    "/courses/{course_id}/lessons",
    response_model=LessonRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    lesson_data: LessonCreate, db: DatabaseSession, course: OwnedCourse
) -> LessonRead:
    return lesson_service.create_lesson(db, course, lesson_data)


@router.get("/courses/{course_id}/lessons", response_model=list[LessonRead])
def list_lessons(course_id: uuid.UUID, db: DatabaseSession) -> list[LessonRead]:
    if get_course(db, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return lesson_service.list_course_lessons(db, course_id)


@router.get("/lessons/{lesson_id}", response_model=LessonRead)
def read_lesson(lesson_id: uuid.UUID, db: DatabaseSession) -> LessonRead:
    lesson = lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=LessonRead)
def update_lesson(
    lesson_data: LessonUpdate, db: DatabaseSession, lesson: OwnedLesson
) -> LessonRead:
    return lesson_service.update_lesson(db, lesson, lesson_data)


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(db: DatabaseSession, lesson: OwnedLesson) -> Response:
    try:
        lesson_service.delete_lesson(db, lesson)
    except lesson_service.LessonDeleteConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lesson cannot be deleted because it has protected learning history",
        ) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
