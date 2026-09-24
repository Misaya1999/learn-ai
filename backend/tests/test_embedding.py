from types import SimpleNamespace

import pytest

from app.services.embedding import (
    EmbeddingDimensionError,
    EmbeddingProviderError,
    OpenAIEmbeddingService,
)


class FakeEmbeddingsResource:
    def __init__(self, responses=None, error: Exception | None = None) -> None:
        self.responses = list(responses or [])
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.responses.pop(0)


def make_client(resource: FakeEmbeddingsResource):
    return SimpleNamespace(embeddings=resource)


def test_embedding_service_preserves_input_order_and_batches() -> None:
    first = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=[2.0, 0.0, 0.0]),
            SimpleNamespace(index=0, embedding=[1.0, 0.0, 0.0]),
        ]
    )
    second = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=[3.0, 0.0, 0.0])]
    )
    resource = FakeEmbeddingsResource([first, second])
    service = OpenAIEmbeddingService(
        api_key="test",
        model="text-embedding-3-small",
        dimensions=3,
        batch_size=2,
        client=make_client(resource),
    )

    result = service.embed_texts(["first", "second", "third"])

    assert result == [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]
    assert [call["input"] for call in resource.calls] == [
        ["first", "second"],
        ["third"],
    ]


def test_embedding_dimension_is_validated() -> None:
    response = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=[1.0, 2.0])]
    )
    service = OpenAIEmbeddingService(
        api_key="test",
        model="text-embedding-3-small",
        dimensions=3,
        batch_size=10,
        client=make_client(FakeEmbeddingsResource([response])),
    )

    with pytest.raises(EmbeddingDimensionError):
        service.embed_text("dimension mismatch")


@pytest.mark.parametrize("texts", [[], [""], ["   "]])
def test_empty_embedding_input_is_rejected(texts: list[str]) -> None:
    service = OpenAIEmbeddingService(
        api_key="test",
        model="text-embedding-3-small",
        dimensions=3,
        batch_size=10,
        client=make_client(FakeEmbeddingsResource()),
    )

    with pytest.raises(ValueError):
        service.embed_texts(texts)


def test_provider_failure_is_sanitized() -> None:
    service = OpenAIEmbeddingService(
        api_key="test",
        model="text-embedding-3-small",
        dimensions=3,
        batch_size=10,
        client=make_client(
            FakeEmbeddingsResource(error=RuntimeError("raw provider secret detail"))
        ),
    )

    with pytest.raises(EmbeddingProviderError, match="Embedding provider request failed"):
        service.embed_text("safe input")
