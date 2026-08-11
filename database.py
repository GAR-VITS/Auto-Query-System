"""
PostgreSQL access layer.

Two responsibilities:
1. Introspect the schema (tables/columns/FKs) so it can be embedded into ChromaDB.
2. Execute generated SQL safely (read-only by default, row-limited).
"""
from __future__ import annotations

import re
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings

settings = get_settings()

# Only these statement types are allowed to run automatically.
# Anything else (INSERT/UPDATE/DELETE/DDL) is routed to the Phase 3
# "approved business actions" path, which is out of scope for this
# read/explain pipeline and must go through an explicit approval step.
_READ_ONLY_PATTERN = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


class UnsafeSQLError(Exception):
    """Raised when generated SQL isn't a read-only statement."""


def get_connection() -> psycopg.Connection:
    return psycopg.connect(settings.postgres_dsn, row_factory=dict_row)


def fetch_schema_snapshot() -> list[dict[str, Any]]:
    """
    Pulls table/column/type/FK info from information_schema.
    This is what gets chunked and embedded into ChromaDB so the
    Query Agent has "nearest context" to ground SQL generation on.
    """
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


def schema_snapshot_to_documents(snapshot: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Groups the flat column rows into one text 'document' per table,
    ready for embedding. Each doc reads like:

        Table: customers
        Columns: id (integer, PK), name (text), signup_date (date)
        Foreign keys: none
    """
    tables: dict[str, dict[str, Any]] = {}
    for row in snapshot:
        t = tables.setdefault(row["table_name"], {"columns": [], "fks": []})
        col_desc = f'{row["column_name"]} ({row["data_type"]}'
        if row["constraint_type"] == "PRIMARY KEY":
            col_desc += ", PK"
        col_desc += ")"
        if col_desc not in t["columns"]:
            t["columns"].append(col_desc)
        if row["constraint_type"] == "FOREIGN KEY" and row["references_table"]:
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
    """
    Executes a single read-only SQL statement.
    Raises UnsafeSQLError if the statement isn't SELECT/WITH.
    Raises psycopg.Error on syntax/semantic errors — the caller
    (Query Agent) catches that to drive the self-correction loop.
    """
    if not _READ_ONLY_PATTERN.match(sql):
        raise UnsafeSQLError(
            "Only read-only SELECT/WITH statements are auto-executed. "
            "Write actions require the approved-action workflow (Phase 3)."
        )

    limit = row_limit or settings.query_row_limit
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchmany(limit)
        columns = [d.name for d in cur.description] if cur.description else []
        return rows, columns
