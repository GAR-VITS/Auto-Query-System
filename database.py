"""
PostgreSQL and SQLite access layer.
Introspects schema and safely executes read-only SQL queries.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any

import psycopg
from psycopg.rows import dict_row

try:
    from config import get_settings
except ImportError:
    from app.core.config import get_settings

settings = get_settings()
_READ_ONLY_PATTERN = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


class UnsafeSQLError(Exception):
    """Raised when generated SQL isn't a read-only statement."""


def get_connection() -> psycopg.Connection:
    return psycopg.connect(settings.postgres_dsn, row_factory=dict_row)


def fetch_schema_snapshot() -> list[dict[str, Any]]:
    """Pulls table/column/type info from Postgres or SQLite."""
    try:
        query = """
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                tc.constraint_type,
                ccu.table_name AS references_table,
                ccu.column_name AS references_column
            FROM information_schema.columns c
            LEFT JOIN information_schema.key_column_usage kcu
                ON c.table_name = kcu.table_name AND c.column_name = kcu.column_name
            LEFT JOIN information_schema.table_constraints tc
                ON kcu.constraint_name = tc.constraint_name
                AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
            LEFT JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                AND tc.constraint_type = 'FOREIGN KEY'
            WHERE c.table_schema = 'public'
            ORDER BY c.table_name, c.ordinal_position;
        """
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    except Exception:
        # Fallback to SQLite schema inspection
        if settings.sqlite_db_path.exists():
            conn = sqlite3.connect(str(settings.sqlite_db_path))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [r[0] for r in cur.fetchall()]
            rows = []
            for t in tables:
                cur.execute(f"PRAGMA table_info('{t}');")
                for col in cur.fetchall():
                    rows.append({
                        "table_name": t,
                        "column_name": col[1],
                        "data_type": col[2],
                        "is_nullable": "YES" if not col[3] else "NO",
                        "constraint_type": "PRIMARY KEY" if col[5] else None,
                        "references_table": None,
                        "references_column": None,
                    })
            conn.close()
            return rows
        return []


def schema_snapshot_to_documents(snapshot: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    for row in snapshot:
        t = tables.setdefault(row["table_name"], {"columns": [], "fks": []})
        col_desc = f'{row["column_name"]} ({row["data_type"]}'
        if row.get("constraint_type") == "PRIMARY KEY":
            col_desc += ", PK"
        col_desc += ")"
        if col_desc not in t["columns"]:
            t["columns"].append(col_desc)
        if row.get("constraint_type") == "FOREIGN KEY" and row.get("references_table"):
            fk = f'{row["column_name"]} -> {row["references_table"]}.{row["references_column"]}'
            if fk not in t["fks"]:
                t["fks"].append(fk)

    documents = []
    for table_name, info in tables.items():
        text = (
            f"Table: {table_name}\n"
            f"Columns: {', '.join(info['columns'])}\n"
            f"Foreign keys: {', '.join(info['fks']) if info['fks'] else 'none'}"
        )
        documents.append({"id": f"table::{table_name}", "text": text, "table_name": table_name})
    return documents


def execute_sql(sql: str, row_limit: int | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    if not _READ_ONLY_PATTERN.match(sql):
        raise UnsafeSQLError("Only read-only SELECT/WITH statements are auto-executed.")

    limit = row_limit or settings.query_row_limit
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchmany(limit)
            columns = [d.name for d in cur.description] if cur.description else []
            return rows, columns
    except Exception:
        # SQLite execution fallback
        conn = sqlite3.connect(str(settings.sqlite_db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows_raw = cur.fetchmany(limit)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(r) for r in rows_raw]
        conn.close()
        return rows, columns
