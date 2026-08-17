"""Service-local configuration with no serializable global settings object."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated service-local runtime settings loaded only when the app is created."""

    model_config = SettingsConfigDict(env_prefix="{{ENV_PREFIX}}", extra="forbid")

    service_name: ClassVar[str] = "{{SERVICE_NAME}}"
    service_version: ClassVar[str] = "0.1.0"

    environment: Literal["development", "test", "production"]
    instance_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    http_connect_timeout_seconds: float = Field(gt=0, le=10)
    http_read_timeout_seconds: float = Field(gt=0, le=30)
    http_write_timeout_seconds: float = Field(gt=0, le=30)
    http_pool_timeout_seconds: float = Field(gt=0, le=10)
    http_max_connections: int = Field(ge=1, le=100)
    http_max_keepalive_connections: int = Field(ge=0, le=100)
