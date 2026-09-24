from typing import Protocol

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.quiz import GeneratedQuiz


class QuizGenerationError(RuntimeError):
    pass


class QuizGenerationConfigurationError(QuizGenerationError):
    pass


class QuizGenerationProviderError(QuizGenerationError):
    pass


class QuizGenerationValidationError(QuizGenerationError):
    pass


class QuizGenerationService(Protocol):
    def generate_quiz(self, *, instructions: str, input_text: str) -> GeneratedQuiz: ...


class OpenAIQuizGenerationService:
    def __init__(self, *, api_key: str | None, model: str, max_output_tokens: int, client: OpenAI | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.max_output_tokens = max_output_tokens
        self._client = client

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise QuizGenerationConfigurationError("Quiz generation provider is not configured")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate_quiz(self, *, instructions: str, input_text: str) -> GeneratedQuiz:
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=instructions,
                input=input_text,
                text_format=GeneratedQuiz,
                max_output_tokens=self.max_output_tokens,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise QuizGenerationProviderError("Quiz provider returned no structured output")
            return GeneratedQuiz.model_validate(parsed.model_dump())
        except QuizGenerationError:
            raise
        except ValidationError as exc:
            raise QuizGenerationValidationError("Quiz provider returned invalid output") from exc
        except Exception as exc:
            raise QuizGenerationProviderError("Quiz provider request failed") from exc


def get_quiz_generation_service() -> QuizGenerationService:
    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    return OpenAIQuizGenerationService(
        api_key=api_key,
        model=settings.openai_chat_model,
        max_output_tokens=settings.quiz_generation_max_output_tokens,
    )
