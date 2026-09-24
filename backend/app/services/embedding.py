from typing import Protocol, Sequence

from openai import OpenAI

from app.core.config import settings


class EmbeddingServiceError(RuntimeError):
    pass


class EmbeddingConfigurationError(EmbeddingServiceError):
    pass


class EmbeddingProviderError(EmbeddingServiceError):
    pass


class EmbeddingDimensionError(EmbeddingServiceError):
    pass


class EmbeddingService(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_text(self, text: str) -> list[float]: ...


class OpenAIEmbeddingService:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        dimensions: int,
        batch_size: int,
        client: OpenAI | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size
        self._client = client

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise EmbeddingConfigurationError(
                    "Embedding provider is not configured"
                )
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        prepared = [text.strip() for text in texts]
        if not prepared:
            raise ValueError("At least one text value is required")
        if any(not text for text in prepared):
            raise ValueError("Embedding input must not be empty")

        embeddings: list[list[float]] = []
        for start in range(0, len(prepared), self.batch_size):
            batch = prepared[start : start + self.batch_size]
            try:
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model,
                    dimensions=self.dimensions,
                    encoding_format="float",
                )
            except EmbeddingServiceError:
                raise
            except Exception as exc:
                raise EmbeddingProviderError(
                    "Embedding provider request failed"
                ) from exc

            ordered = sorted(response.data, key=lambda item: item.index)
            if [item.index for item in ordered] != list(range(len(batch))):
                raise EmbeddingProviderError("Embedding provider returned invalid ordering")
            for item in ordered:
                vector = list(item.embedding)
                if len(vector) != self.dimensions:
                    raise EmbeddingDimensionError(
                        "Embedding provider returned an unexpected vector dimension"
                    )
                embeddings.append(vector)

        if len(embeddings) != len(prepared):
            raise EmbeddingProviderError("Embedding provider returned an invalid result count")
        return embeddings


def get_embedding_service() -> EmbeddingService:
    api_key = (
        settings.openai_api_key.get_secret_value()
        if settings.openai_api_key is not None
        else None
    )
    return OpenAIEmbeddingService(
        api_key=api_key,
        model=settings.openai_embedding_model,
        dimensions=settings.openai_embedding_dimensions,
        batch_size=settings.openai_embedding_batch_size,
    )
