from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from psycopg import connect, sql

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
SCHEMA_FILE = BASE_DIR / "schema.sql"

load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/enterprise_finance",
)


def main() -> None:
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")

    print(f"Using database URL: {DATABASE_URL}")
    print(f"Applying schema from: {SCHEMA_FILE}")

    script = SCHEMA_FILE.read_text(encoding="utf-8")
    with connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(script)

    print("Database schema created successfully.")


if __name__ == "__main__":
    main()
