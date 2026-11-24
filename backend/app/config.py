import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database URLs
    database_url_owner: str = Field(
        default="postgresql+psycopg://nexus_owner:owner_secret@localhost:5432/nexus",
        validation_alias="DATABASE_URL_OWNER",
    )
    database_url_reader: str = Field(
        default="postgresql+psycopg://nexus_reader:reader_secret@localhost:5432/nexus",
        validation_alias="DATABASE_URL_READER",
    )
    database_url_writer: str = Field(
        default="postgresql+psycopg://nexus_writer:writer_secret@localhost:5432/nexus",
        validation_alias="DATABASE_URL_WRITER",
    )

    # SQLite local fallback DB path for offline & local testing
    sqlite_db_path: Path = Path(__file__).resolve().parent.parent / "db" / "nexus_local.db"

    # Security & JWT
    jwt_secret: str = Field(default="nexusdb-super-secret-key-32-chars-long", validation_alias="JWT_SECRET")
    jwt_expire_minutes: int = Field(default=60, validation_alias="JWT_EXPIRE_MINUTES")
    jwt_algorithm: str = "HS256"

    # LLM configuration
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")

    # Semantic Memory & ChromaDB
    embedding_backend: str = Field(default="local", validation_alias="EMBEDDING_BACKEND")
    chroma_path: str = Field(default="./.chroma", validation_alias="CHROMA_PATH")
    top_k_schema_slices: int = Field(default=8, validation_alias="TOP_K_SCHEMA_SLICES")

    # Execution & Reflection Loop
    demo_mode: bool = Field(default=True, validation_alias="DEMO_MODE")
    max_retries: int = Field(default=3, validation_alias="MAX_RETRIES")
    statement_timeout_ms: int = Field(default=5000, validation_alias="STATEMENT_TIMEOUT_MS")
    row_cap: int = Field(default=1000, validation_alias="ROW_CAP")

    # Rate Limiting
    rate_limit_per_minute: int = 30

    # Action parameters
    max_action_rows: int = 25
    confirmation_token_expiry_seconds: int = 120

    # Networking
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
