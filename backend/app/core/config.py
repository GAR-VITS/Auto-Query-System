import os
from functools import lru_cache
from pathlib import Path
from typing import List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# Load .env from root or backend
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self):
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/enterprise_finance",
        )
        self.sqlite_db_path: Path = BASE_DIR / "db" / "enterprise_finance.db"
        self.schema_file_path: Path = BASE_DIR / "db" / "schema.sql"
        self.max_self_correction_attempts: int = int(
            os.getenv("MAX_SELF_CORRECTION_ATTEMPTS", "3")
        )
        self.enable_voice_input: bool = (
            os.getenv("ENABLE_VOICE_INPUT", "true").lower() == "true"
        )
        self.port: int = int(os.getenv("PORT", "8000"))

        # CORS Allowed Origins
        allowed_raw = os.getenv("ALLOWED_ORIGINS", "*")
        if allowed_raw.strip() == "*":
            self.allowed_origins: List[str] = ["*"]
        else:
            self.allowed_origins: List[str] = [
                origin.strip() for origin in allowed_raw.split(",") if origin.strip()
            ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
