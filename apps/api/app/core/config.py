"""Validated application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed API settings with safe local defaults."""

    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        env_prefix="MSME_SAARTHI_",
        extra="ignore",
    )

    app_name: str = "MSME Saarthi API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    request_id_header: str = Field(default="X-Request-ID", min_length=1, max_length=64)
    database_url: str | None = None
    data_encryption_key: SecretStr | None = None
    data_encryption_key_version: str = Field(default="v1", pattern=r"^v[1-9][0-9]*$")
    web_origin: str = "http://127.0.0.1:5173"
    session_cookie_name: str = "msme_saarthi_session"
    session_cookie_secure: bool = True
    session_idle_minutes: int = Field(default=60, ge=5, le=1_440)
    session_absolute_hours: int = Field(default=24, ge=1, le=168)
    llm_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: SecretStr | None = None
    openai_model: str = Field(default="gpt-5.4-mini", min_length=1, max_length=128)
    openai_image_model: str = Field(default="gpt-image-2", min_length=1, max_length=128)
    openai_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0)
    image_generation_timeout_seconds: float = Field(default=120.0, ge=10.0, le=300.0)
    retrieval_provider: Literal["curated", "opensearch"] = "curated"
    embedding_provider: Literal["local", "openai"] = "local"
    embedding_model: str = Field(default="text-embedding-3-small", min_length=1, max_length=128)
    embedding_dimensions: int = Field(default=384, ge=64, le=3_072)
    opensearch_url: str = "http://127.0.0.1:9200"
    opensearch_index: str = Field(default="msme-schemes-v2", pattern=r"^[a-z0-9._-]+$")
    retrieval_official_max_age_days: int = Field(default=90, ge=1, le=3_650)
    retrieval_guide_max_age_days: int = Field(default=3_650, ge=1, le=7_300)
    retrieval_rrf_rank_constant: int = Field(default=60, ge=1, le=1_000)
    retrieval_rrf_lexical_weight: float = Field(default=0.8, gt=0, le=10)
    retrieval_rrf_vector_weight: float = Field(default=1.0, gt=0, le=10)
    retrieval_rrf_max_chunks_per_document: int = Field(default=1, ge=1, le=1_000)


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance per process."""
    return Settings()
