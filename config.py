"""
Central configuration, loaded from environment variables (.env).
Nothing here talks to a network — pure settings object.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- LLM ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"

    # --- Postgres (the business database being queried) ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "business_db"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    # --- ChromaDB (schema + semantic memory) ---
    chroma_persist_dir: str = "./chroma_store"
    chroma_collection_schema: str = "schema_context"
    chroma_collection_history: str = "query_history"

    # --- Agent behavior ---
    max_self_correction_attempts: int = 3
    query_row_limit: int = 500

    # --- Voice ---
    enable_voice_input: bool = False
    whisper_model_size: str = "base"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
