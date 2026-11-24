"""
NexusDB SQL Guard
Uses sqlglot (Postgres dialect) to statically parse, validate, and rewrite SQL before execution.
Enforces read-only safety, catalog validation, and automatic LIMIT capping.
"""

import re
from typing import Any
import sqlglot
from sqlglot import exp
from app.memory.catalog import CatalogSnapshot, get_catalog_snapshot


class GuardVerdict:
    def __init__(self, ok: bool, sql: str = "", error_message: str = "", error_code: str = ""):
        self.ok = ok
        self.sql = sql
        self.error_message = error_message
        self.error_code = error_code

    def __bool__(self) -> bool:
        return self.ok


FORBIDDEN_FUNCTIONS = {
    "pg_sleep", "pg_read_file", "pg_read_binary_file", "pg_ls_dir",
    "dblink", "dblink_exec", "lo_import", "lo_export", "lo_unlink",
    "query_to_xml", "pg_terminate_backend"
}

FORBIDDEN_CATALOGS = {
    "information_schema", "pg_catalog", "pg_tables", "pg_class", "pg_stat_activity",
    "pg_user", "pg_shadow", "pg_authid", "pg_database", "sqlite_master", "sqlite_schema"
}


class SqlGuard:
    def __init__(self, default_limit: int = 1000, max_limit: int = 1000):
        self.default_limit = default_limit
        self.max_limit = max_limit

    def check(self, sql_query: str, catalog: CatalogSnapshot | None = None) -> GuardVerdict:
        if not sql_query or not sql_query.strip():
            return GuardVerdict(ok=False, error_message="Empty query rejected.", error_code="EMPTY_QUERY")

        cleaned = sql_query.strip().rstrip(";")

        # 1. Multi-statement check before/during parse
        # Check raw string for comment tricks or statement terminators
        raw_statements = [s for s in cleaned.split(";") if s.strip()]
        if len(raw_statements) > 1:
            return GuardVerdict(
                ok=False,
                error_message="Multiple SQL statements rejected. NexusDB only executes single SELECT statements.",
                error_code="MULTIPLE_STATEMENTS"
            )

        # 2. Parse with sqlglot (postgres dialect)
        try:
            parsed_trees = sqlglot.parse(cleaned, read="postgres")
        except Exception as e:
            return GuardVerdict(
                ok=False,
                error_message=f"SQL syntax error: {str(e)}",
                error_code="SYNTAX_ERROR"
            )

        if len(parsed_trees) > 1:
            return GuardVerdict(
                ok=False,
                error_message="Multiple statements detected after AST parsing.",
                error_code="MULTIPLE_STATEMENTS"
            )

        if not parsed_trees or parsed_trees[0] is None:
            return GuardVerdict(ok=False, error_message="Failed to parse SQL AST.", error_code="PARSE_FAILED")

        expression = parsed_trees[0]

        # 3. Must be a SELECT expression (no INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, etc.)
        if not isinstance(expression, (exp.Select, exp.Union)):
            return GuardVerdict(
                ok=False,
                error_message=f"Query type {type(expression).__name__} prohibited. Only SELECT queries are permitted.",
                error_code="UNAUTHORIZED_COMMAND"
            )

        # Check for DML / DDL anywhere in expression tree (including CTEs or subqueries)
        for node in expression.walk():
            if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command)):
                return GuardVerdict(
                    ok=False,
                    error_message="Prohibited DDL/DML detected inside query or CTE.",
                    error_code="DDL_DML_PROHIBITED"
                )
            
            # Check for SELECT INTO
            if isinstance(node, exp.Into):
                return GuardVerdict(
                    ok=False,
                    error_message="SELECT INTO statement prohibited.",
                    error_code="SELECT_INTO_PROHIBITED"
                )

            # Check for COPY
            if isinstance(node, exp.Copy):
                return GuardVerdict(
                    ok=False,
                    error_message="COPY statement prohibited.",
                    error_code="COPY_PROHIBITED"
                )

            # Check for forbidden functions (e.g. pg_sleep, dblink, lo_*)
            if isinstance(node, exp.Anonymous):
                fn_name = node.this.lower()
                if fn_name in FORBIDDEN_FUNCTIONS or fn_name.startswith("lo_"):
                    return GuardVerdict(
                        ok=False,
                        error_message=f"Function {fn_name}() prohibited for security.",
                        error_code="DANGEROUS_FUNCTION"
                    )

        # 4. Catalog & Table/Column validation
        active_cat = catalog or get_catalog_snapshot()
        table_aliases: dict[str, str] = {}

        # First collect all tables and their aliases
        for table_node in expression.find_all(exp.Table):
            tbl_name = table_node.name.lower()
            db_name = (table_node.db or "").lower()
            alias = table_node.alias.lower() if table_node.alias else tbl_name

            # Check system catalogs
            if tbl_name in FORBIDDEN_CATALOGS or db_name in FORBIDDEN_CATALOGS or tbl_name.startswith("pg_") or db_name.startswith("pg_"):
                return GuardVerdict(
                    ok=False,
                    error_message=f"Access to system catalog {db_name or tbl_name} is prohibited.",
                    error_code="SYSTEM_CATALOG_ACCESS"
                )

            if not active_cat.has_table(tbl_name):
                return GuardVerdict(
                    ok=False,
                    error_message=f"Table '{tbl_name}' does not exist in schema catalog.",
                    error_code="UNKNOWN_TABLE"
                )

            table_aliases[alias] = tbl_name
            table_aliases[tbl_name] = tbl_name

        # Verify referenced columns if qualified
        for col_node in expression.find_all(exp.Column):
            col_name = col_node.name.lower()
            tbl_ref = col_node.table.lower() if col_node.table else None

            # Ignore star expressions
            if col_name == "*":
                continue

            if tbl_ref and tbl_ref in table_aliases:
                real_tbl = table_aliases[tbl_ref]
                if not active_cat.has_column(real_tbl, col_name):
                    return GuardVerdict(
                        ok=False,
                        error_message=f"Column '{tbl_ref}.{col_name}' does not exist on table '{real_tbl}'.",
                        error_code="UNKNOWN_COLUMN"
                    )

        # 5. Automatic LIMIT Enforcement
        limit_node = expression.args.get("limit")
        if limit_node is None:
            expression = expression.limit(self.default_limit)
        else:
            try:
                lim_expr = limit_node.expression
                lim_val = int(lim_expr.this if hasattr(lim_expr, "this") else str(lim_expr))
                if lim_val > self.max_limit:
                    if hasattr(lim_expr, "this"):
                        lim_expr.this = str(self.max_limit)
                    else:
                        expression.set("limit", exp.Limit(expression=exp.Literal.number(self.max_limit)))
            except Exception:
                expression.set("limit", exp.Limit(expression=exp.Literal.number(self.max_limit)))

        safe_sql = expression.sql(dialect="postgres")
        return GuardVerdict(ok=True, sql=safe_sql)


_guard_instance: SqlGuard | None = None


def get_sql_guard() -> SqlGuard:
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = SqlGuard()
    return _guard_instance
