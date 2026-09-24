import uuid

from fastapi import APIRouter

from app.api.dependencies import DatabaseSession, OwnedCourse, StudentUser
from app.schemas.analytics import (
    CourseAnalyticsOverview, CourseLessonAnalytics, CourseQuestionAnalytics,
    CourseStudentAnalytics, StudentAnalyticsOverview, StudentLessonAnalytics,
    StudentProgressPoint,
)
from app.services import analytics as analytics_service

router = APIRouter(tags=["analytics"])


@router.get("/users/me/analytics", response_model=StudentAnalyticsOverview)
def my_analytics(db: DatabaseSession, student: StudentUser):
    return analytics_service.student_overview(db, student.id)


@router.get("/users/me/analytics/lessons", response_model=list[StudentLessonAnalytics])
def my_lesson_analytics(db: DatabaseSession, student: StudentUser):
    return analytics_service.student_lessons(db, student.id)


@router.get("/users/me/analytics/progress", response_model=list[StudentProgressPoint])
def my_progress(db: DatabaseSession, student: StudentUser):
    return analytics_service.student_progress(db, student.id)


@router.get("/courses/{course_id}/analytics", response_model=CourseAnalyticsOverview)
def course_analytics(course_id: uuid.UUID, db: DatabaseSession, course: OwnedCourse):
    return analytics_service.course_overview(db, course.id)


@router.get("/courses/{course_id}/analytics/students", response_model=list[CourseStudentAnalytics])
def course_student_analytics(course_id: uuid.UUID, db: DatabaseSession, course: OwnedCourse):
    return analytics_service.course_students(db, course.id)


@router.get("/courses/{course_id}/analytics/lessons", response_model=list[CourseLessonAnalytics])
def course_lesson_analytics(course_id: uuid.UUID, db: DatabaseSession, course: OwnedCourse):
    return analytics_service.course_lessons(db, course.id)


@router.get("/courses/{course_id}/analytics/questions", response_model=list[CourseQuestionAnalytics])
def course_question_analytics(course_id: uuid.UUID, db: DatabaseSession, course: OwnedCourse):
    return analytics_service.course_questions(db, course.id)
