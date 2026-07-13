"""Validated application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed API settings with safe local defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
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


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance per process."""
    return Settings()
