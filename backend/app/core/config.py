from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "LearnAI API"
    app_env: str = "development"
    app_debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str
    backend_cors_origins: list[AnyHttpUrl] = [AnyHttpUrl("http://localhost:3000")]
    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    document_storage_dir: Path = Path("backend/storage/documents")
    document_max_upload_size: int = Field(default=10 * 1024 * 1024, gt=0)
    document_chunk_size: int = Field(default=1000, gt=0)
    document_chunk_overlap: int = Field(default=200, ge=0)
    openai_api_key: SecretStr | None = None
    openai_embedding_model: Literal["text-embedding-3-small"] = (
        "text-embedding-3-small"
    )
    openai_embedding_dimensions: Literal[1536] = 1536
    openai_embedding_batch_size: int = Field(default=100, ge=1, le=2048)
    openai_chat_model: str = Field(default="gpt-4.1-mini", min_length=1)
    ai_tutor_max_output_tokens: int = Field(default=500, ge=1, le=4096)
    ai_tutor_retrieval_top_k: int = Field(default=5, ge=1, le=20)
    ai_tutor_max_context_characters: int = Field(default=12000, ge=1)
    quiz_generation_max_context_characters: int = Field(default=16000, ge=1)
    quiz_generation_max_output_tokens: int = Field(default=4000, ge=1, le=16000)

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_chunk_configuration(self) -> "Settings":
        if self.document_chunk_overlap >= self.document_chunk_size:
            raise ValueError("DOCUMENT_CHUNK_OVERLAP must be smaller than DOCUMENT_CHUNK_SIZE")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
