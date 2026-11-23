"""
NexusDB Read-Only SQL Executor
Enforces read-only transactions, statement timeout (5000ms), and 1000-row cap.
"""

import asyncio
import time
import sqlite3
from typing import Any
from sqlalchemy import text

from app.config import get_settings
from app.db.session import is_postgres_available, get_db_connection

settings = get_settings()


class ExecutionResult:
    def __init__(self, columns: list[str], rows: list[list[Any]], row_count: int, truncated: bool, execution_ms: float):
        self.columns = columns
        self.rows = rows
        self.row_count = row_count
        self.truncated = truncated
        self.execution_ms = execution_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "truncated": self.truncated,
            "execution_ms": self.execution_ms,
        }


class SqlExecutor:
    def __init__(self, role: str = "nexus_reader", timeout_ms: int = 5000, row_cap: int = 1000):
        self.role = role
        self.timeout_ms = timeout_ms
        self.row_cap = row_cap

    def run_sync(self, sql: str) -> ExecutionResult:
        start_ts = time.time()
        sql_stripped = sql.strip().rstrip(";")

        # Security check at executor level: nexus_reader cannot execute writes
        if self.role == "nexus_reader":
            upper_sql = sql_stripped.upper()
            first_word = upper_sql.split()[0] if upper_sql.split() else ""
            if first_word in ("UPDATE", "INSERT", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE"):
                raise PermissionError(f"Permission denied: role nexus_reader is strictly READ-ONLY. Cannot execute {first_word}.")

        if is_postgres_available():
            with get_db_connection(self.role) as conn:
                # Set transaction read only and statement timeout
                conn.execute(text(f"SET statement_timeout = {self.timeout_ms}"))
                if self.role == "nexus_reader":
                    conn.execute(text("SET TRANSACTION READ ONLY"))
                cursor = conn.execute(text(sql_stripped))
                columns = list(cursor.keys()) if cursor.returns_rows else []
                raw_rows = cursor.fetchmany(self.row_cap + 1) if cursor.returns_rows else []
                truncated = len(raw_rows) > self.row_cap
                rows = [list(r) for r in raw_rows[:self.row_cap]]
        else:
            with get_db_connection(self.role) as conn:
                cur = conn.cursor()
                # Simulate timeout or query execution
                cur.execute(sql_stripped)
                if cur.description:
                    columns = [d[0] for d in cur.description]
                    raw_rows = cur.fetchmany(self.row_cap + 1)
                    truncated = len(raw_rows) > self.row_cap
                    rows = [list(r) for r in raw_rows[:self.row_cap]]
                else:
                    columns = []
                    rows = []
                    truncated = False

        duration_ms = round((time.time() - start_ts) * 1000, 2)
        return ExecutionResult(columns=columns, rows=rows, row_count=len(rows), truncated=truncated, execution_ms=duration_ms)

    async def run(self, sql: str) -> ExecutionResult:
        # Run synchronous DB I/O in thread pool with strict timeout
        return await asyncio.wait_for(
            asyncio.to_thread(self.run_sync, sql),
            timeout=self.timeout_ms / 1000.0,
        )
