"""Application settings using Pydantic Settings."""
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_name: str = "magure-ai-platform"

    # Temporal
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "agent-tasks"

    # PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://magure:magure_dev_password@localhost:5432/magure_db"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # LLM Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Security
    secret_key: str = "dev-secret-key-change-in-production"

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Vault / Secrets Management
    vault_provider: Literal["local", "hashicorp", "aws", "azure"] = "local"
    secrets_encryption_key: Optional[str] = None  # Fernet key for local vault
    secrets_storage_path: Optional[str] = None  # Path for local vault storage
    vault_url: Optional[str] = None  # HashiCorp Vault URL
    vault_token: Optional[str] = None  # HashiCorp Vault token
    aws_secrets_region: Optional[str] = None  # AWS Secrets Manager region

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
