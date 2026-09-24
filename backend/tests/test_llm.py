from types import SimpleNamespace

import pytest

from app.services.llm import (
    LLMConfigurationError,
    LLMProviderError,
    OpenAIAnswerGenerationService,
)


class FakeResponses:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def test_openai_answer_service_uses_responses_api() -> None:
    responses = FakeResponses(SimpleNamespace(output_text="  Grounded answer.  "))
    client = SimpleNamespace(responses=responses)
    service = OpenAIAnswerGenerationService(
        api_key=None, model="test-model", max_output_tokens=123, client=client
    )

    answer = service.generate_answer(instructions="rules", input_text="context")

    assert answer == "Grounded answer."
    assert responses.calls == [
        {
            "model": "test-model",
            "instructions": "rules",
            "input": "context",
            "max_output_tokens": 123,
        }
    ]


def test_answer_service_does_not_require_key_until_called() -> None:
    service = OpenAIAnswerGenerationService(
        api_key=None, model="test-model", max_output_tokens=123
    )
    with pytest.raises(LLMConfigurationError, match="not configured"):
        service.generate_answer(instructions="rules", input_text="context")


def test_answer_provider_failure_is_sanitized() -> None:
    responses = FakeResponses(error=RuntimeError("secret upstream detail"))
    service = OpenAIAnswerGenerationService(
        api_key=None,
        model="test-model",
        max_output_tokens=123,
        client=SimpleNamespace(responses=responses),
    )
    with pytest.raises(LLMProviderError, match="request failed") as error:
        service.generate_answer(instructions="rules", input_text="context")
    assert "secret upstream detail" not in str(error.value)


def test_empty_provider_output_is_rejected() -> None:
    service = OpenAIAnswerGenerationService(
        api_key=None,
        model="test-model",
        max_output_tokens=123,
        client=SimpleNamespace(
            responses=FakeResponses(SimpleNamespace(output_text="   "))
        ),
    )
    with pytest.raises(LLMProviderError, match="empty response"):
        service.generate_answer(instructions="rules", input_text="context")
