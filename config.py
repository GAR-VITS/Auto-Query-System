"""
Central configuration, loaded from environment variables (.env).
"""
import os
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    def __init__(self):
        # --- LLM ---
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # --- Postgres ---
        self.postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
        self.postgres_db: str = os.getenv("POSTGRES_DB", "enterprise_finance")
        self.postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
        self.postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}",
        )

        # --- SQLite Fallback ---
        self.sqlite_db_path: Path = ROOT_DIR / "backend" / "db" / "enterprise_finance.db"
        self.schema_file_path: Path = ROOT_DIR / "backend" / "db" / "schema.sql"

        # --- ChromaDB ---
        self.chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
        self.chroma_collection_schema: str = "schema_context"
        self.chroma_collection_history: str = "query_history"

        # --- Agent behavior ---
        self.max_self_correction_attempts: int = int(
            os.getenv("MAX_SELF_CORRECTION_ATTEMPTS", "3")
        )
        self.query_row_limit: int = int(os.getenv("QUERY_ROW_LIMIT", "500"))

        # --- Voice ---
        self.enable_voice_input: bool = (
            os.getenv("ENABLE_VOICE_INPUT", "true").lower() == "true"
        )
        self.whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "base")

    @property
    def postgres_dsn(self) -> str:
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
