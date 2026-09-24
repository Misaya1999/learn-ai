from types import SimpleNamespace

import pytest

from app.schemas.quiz import GeneratedQuiz
from app.services.quiz_generation import (
    OpenAIQuizGenerationService,
    QuizGenerationConfigurationError,
    QuizGenerationProviderError,
)


class FakeResponses:
    def __init__(self, parsed=None, error=None):
        self.parsed, self.error, self.calls = parsed, error, []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(output_parsed=self.parsed)


def valid_quiz():
    return GeneratedQuiz.model_validate({"questions": [{
        "question_text": "What is labeled learning?", "explanation": "The lesson defines it.",
        "options": [
            {"option_text": "Supervised", "is_correct": True},
            {"option_text": "Unsupervised", "is_correct": False},
            {"option_text": "Random", "is_correct": False},
            {"option_text": "None", "is_correct": False},
        ],
    }]})


def test_openai_quiz_generator_uses_structured_responses_parse():
    responses = FakeResponses(valid_quiz())
    service = OpenAIQuizGenerationService(api_key=None, model="test-model", max_output_tokens=500, client=SimpleNamespace(responses=responses))
    result = service.generate_quiz(instructions="rules", input_text="material")
    assert len(result.questions) == 1
    assert responses.calls[0]["text_format"] is GeneratedQuiz
    assert responses.calls[0]["model"] == "test-model"


def test_quiz_generator_is_lazy_without_api_key():
    service = OpenAIQuizGenerationService(api_key=None, model="test", max_output_tokens=10)
    with pytest.raises(QuizGenerationConfigurationError):
        service.generate_quiz(instructions="rules", input_text="material")


def test_quiz_provider_error_is_sanitized():
    service = OpenAIQuizGenerationService(api_key=None, model="test", max_output_tokens=10, client=SimpleNamespace(responses=FakeResponses(error=RuntimeError("provider secret"))))
    with pytest.raises(QuizGenerationProviderError) as error:
        service.generate_quiz(instructions="rules", input_text="material")
    assert "provider secret" not in str(error.value)
