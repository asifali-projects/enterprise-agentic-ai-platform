from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise Agentic AI Operating Platform"
    environment: str = "development"
    secret_key: str = Field(min_length=32)
    access_token_minutes: int = 30
    database_url: str = "postgresql+asyncpg://agentic:agentic@postgres:5432/agentic"
    redis_url: str = "redis://redis:6379/0"
    cors_origins: list[str] = ["http://localhost:5173"]
    demo_ttl_minutes: int = 120
    invitation_ttl_hours: int = 48
    run_timeout_seconds: int = 120
    max_concurrency: int = 8
    llm_provider: str = "local"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "local-deterministic"
    tool_timeout_seconds: int = 30
    tool_max_retries: int = 2
    tool_allowed_hosts: list[str] = []
    otel_enabled: bool = True
    otel_exporter_endpoint: str = ""
    qdrant_url: str = "http://qdrant:6333"
    memory_vector_size: int = 64
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @field_validator("cors_origins", "tool_allowed_hosts", mode="before")
    @classmethod
    def parse_cors(cls, v):
        return [x.strip() for x in v.split(",")] if isinstance(v, str) else v


settings = Settings()
