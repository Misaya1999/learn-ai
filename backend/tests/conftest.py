import os
import secrets
from collections.abc import Generator
from pathlib import Path

os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(32))
if os.getenv("RUN_POSTGRES_TESTS") != "1":
    os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User  # noqa: F401
from app.services.embedding import get_embedding_service
from app.services.llm import get_answer_generation_service
from app.schemas.quiz import GeneratedQuiz, GeneratedQuizOption, GeneratedQuizQuestion
from app.services.quiz_generation import get_quiz_generation_service


class FakeEmbeddingService:
    def embed_texts(self, texts) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def embed_text(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Embedding input must not be empty")
        vector = [0.0] * 1536
        vector[0] = 1.0
        vector[1] = min(len(text), 1000) / 1000
        return vector


class FakeAnswerGenerationService:
    def generate_answer(self, *, instructions: str, input_text: str) -> str:
        return "A grounded test answer."


class FakeQuizGenerationService:
    def generate_quiz(self, *, instructions: str, input_text: str) -> GeneratedQuiz:
        def question(number: int) -> GeneratedQuizQuestion:
            return GeneratedQuizQuestion(
                question_text=f"Question {number}?",
                explanation=f"Explanation {number} from the lesson.",
                options=[
                    GeneratedQuizOption(option_text=f"Correct {number}", is_correct=True),
                    GeneratedQuizOption(option_text=f"Distractor {number}A", is_correct=False),
                    GeneratedQuizOption(option_text=f"Distractor {number}B", is_correct=False),
                    GeneratedQuizOption(option_text=f"Distractor {number}C", is_correct=False),
                ],
            )
        return GeneratedQuiz(questions=[question(1), question(2)])


@pytest.fixture
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session()

    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_embedding_service] = FakeEmbeddingService
    app.dependency_overrides[get_answer_generation_service] = (
        FakeAnswerGenerationService
    )
    app.dependency_overrides[get_quiz_generation_service] = FakeQuizGenerationService
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
