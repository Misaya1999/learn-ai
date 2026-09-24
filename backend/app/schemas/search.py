import uuid

from pydantic import BaseModel, Field, field_validator


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Query must not be blank")
        return value


class SemanticSearchResult(BaseModel):
    document_id: uuid.UUID
    original_filename: str
    chunk_index: int
    content: str
    similarity: float
