"""Application settings using Pydantic Settings."""
from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import Field, model_validator
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

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins. Set via CORS_ORIGINS env var as comma-separated list.",
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_allow_headers: List[str] = Field(default=["Authorization", "Content-Type", "X-Request-ID"])

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_workflow: str = Field(
        default="10/minute",
        description="Rate limit for workflow execution endpoints",
    )
    rate_limit_agents: str = Field(
        default="20/minute",
        description="Rate limit for agent endpoints",
    )
    rate_limit_default: str = Field(
        default="100/minute",
        description="Default rate limit for all other endpoints",
    )

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

    # JWT Auth
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60  # 1 hour
    jwt_refresh_token_expire_days: int = 7

    # Super User (seeded on first startup)
    superuser_email: Optional[str] = None
    superuser_password: Optional[str] = None

    # Invite expiry
    invite_expire_days: int = 7

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Monitoring
    monitoring_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics collection",
    )
    metrics_prefix: str = Field(
        default="magure",
        description="Prefix for all Prometheus metrics",
    )
    loki_enabled: bool = Field(
        default=False,
        description="Enable Loki log shipping",
    )
    loki_url: str = Field(
        default="http://localhost:3100",
        description="Loki server URL",
    )
    analytics_enabled: bool = Field(
        default=True,
        description="Enable analytics (LLM usage, agent executions) to PostgreSQL",
    )

    # Vault / Secrets Management
    vault_provider: Literal["local", "hashicorp", "aws", "azure"] = "local"
    secrets_encryption_key: Optional[str] = None  # Fernet key for local vault
    secrets_storage_path: Optional[str] = None  # Path for local vault storage
    vault_url: Optional[str] = None  # HashiCorp Vault URL
    vault_token: Optional[str] = None  # HashiCorp Vault token
    aws_secrets_region: Optional[str] = None  # AWS Secrets Manager region

    # Database Connection Pool
    db_pool_size: int = Field(default=5, description="Database connection pool size")
    db_max_overflow: int = Field(default=10, description="Max overflow connections")
    db_pool_recycle: int = Field(default=3600, description="Connection recycle time in seconds")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @model_validator(mode="after")
    def validate_production_config(self) -> "Settings":
        """Validate configuration for production environment."""
        if self.is_production:
            # Ensure secret_key is not the default value
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be changed from default value in production. "
                    "Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )

            # Ensure debug mode is off in production
            if self.app_debug:
                raise ValueError("APP_DEBUG must be False in production")

            # Ensure secrets encryption key is set when using local vault
            if self.vault_provider == "local" and not self.secrets_encryption_key:
                raise ValueError(
                    "SECRETS_ENCRYPTION_KEY is required when using local vault in production. "
                    "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )

            # Warn about wildcard CORS (though we've removed it from defaults)
            if "*" in self.cors_origins:
                raise ValueError(
                    "CORS_ORIGINS cannot contain '*' in production. "
                    "Specify exact origins like 'https://yourdomain.com'"
                )

        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
