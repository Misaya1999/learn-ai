from fastapi import APIRouter

from app.api import analytics, auth, courses, documents, enrollments, lessons, quizzes, search, tutor, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(lessons.router)
api_router.include_router(enrollments.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(tutor.router)
api_router.include_router(quizzes.router)
api_router.include_router(analytics.router)
