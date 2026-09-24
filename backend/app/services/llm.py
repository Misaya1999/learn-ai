from typing import Protocol

from openai import OpenAI

from app.core.config import settings


class LLMServiceError(RuntimeError):
    pass


class LLMConfigurationError(LLMServiceError):
    pass


class LLMProviderError(LLMServiceError):
    pass


class AnswerGenerationService(Protocol):
    def generate_answer(self, *, instructions: str, input_text: str) -> str: ...


class OpenAIAnswerGenerationService:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        max_output_tokens: int,
        client: OpenAI | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_output_tokens = max_output_tokens
        self._client = client

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise LLMConfigurationError("Answer provider is not configured")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate_answer(self, *, instructions: str, input_text: str) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=input_text,
                max_output_tokens=self.max_output_tokens,
            )
        except LLMServiceError:
            raise
        except Exception as exc:
            raise LLMProviderError("Answer provider request failed") from exc

        answer = response.output_text.strip()
        if not answer:
            raise LLMProviderError("Answer provider returned an empty response")
        return answer


def get_answer_generation_service() -> AnswerGenerationService:
    api_key = (
        settings.openai_api_key.get_secret_value()
        if settings.openai_api_key is not None
        else None
    )
    return OpenAIAnswerGenerationService(
        api_key=api_key,
        model=settings.openai_chat_model,
        max_output_tokens=settings.ai_tutor_max_output_tokens,
    )
