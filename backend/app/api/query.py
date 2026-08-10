import os
import re
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import APIRouter
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.schemas.query import QueryRequest, QueryResponse, QueryResult
from app.services.gemini import generate_sql_and_analysis

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/enterprise_finance",
)
SCHEMA_FILE = BASE_DIR / "db" / "schema.sql"

router = APIRouter()

_FORBIDDEN_SQL = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|COPY|EXECUTE)\b",
    re.IGNORECASE,
)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return value


def _serialize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: _serialize_value(val) for key, val in row.items()} for row in rows]


def _validate_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        raise ValueError("Generated SQL is empty.")
    if not re.match(r"^\s*SELECT\b", cleaned, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    if _FORBIDDEN_SQL.search(cleaned):
        raise ValueError("Generated SQL contains forbidden statements.")
    return cleaned


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    start_time = time.time()

    try:
        if not SCHEMA_FILE.exists():
            raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")

        schema_context = SCHEMA_FILE.read_text(encoding="utf-8")
        gemini_data = await generate_sql_and_analysis(request.question, schema_context)
        sql_query = _validate_sql(gemini_data.get("sql", ""))
        analysis = gemini_data.get("analysis", "")

        async with await AsyncConnection.connect(DATABASE_URL) as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql_query)
                columns = [desc.name for desc in cur.description] if cur.description else []
                rows = _serialize_rows(await cur.fetchall())

        execution_time_ms = round((time.time() - start_time) * 1000, 2)

        return QueryResponse(
            success=True,
            result=QueryResult(
                id=f"q-{uuid.uuid4().hex[:12]}",
                question=request.question,
                sql=sql_query,
                columns=columns,
                rows=rows,
                rowCount=len(rows),
                executionTimeMs=execution_time_ms,
                analysis=analysis,
                corrections=0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )

    except Exception as exc:
        return QueryResponse(success=False, error=str(exc))
