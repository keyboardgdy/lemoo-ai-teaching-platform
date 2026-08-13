"""Validated configuration for the non-production Stage 1A skeleton."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment configuration with fail-closed future capabilities."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LEMOO_",
        extra="ignore",
        frozen=True,
    )

    environment: Literal["local", "test", "ci"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    service_name: str = "lemoo-api"
    service_version: str = "0.1.0"
    feature_content: bool = False
    feature_teaching: bool = False
    feature_ai: bool = False
    feature_ota: bool = False
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["127.0.0.1", "localhost", "testserver"]
    )

    @property
    def enabled_future_capabilities(self) -> tuple[str, ...]:
        """Return any future capability that was incorrectly enabled."""

        flags = {
            "content": self.feature_content,
            "teaching": self.feature_teaching,
            "ai": self.feature_ai,
            "ota": self.feature_ota,
        }
        return tuple(name for name, enabled in flags.items() if enabled)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache immutable process settings."""

    return Settings()
