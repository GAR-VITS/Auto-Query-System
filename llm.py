"""
LLM and Gemini integration layer with self-correcting query generation.
"""
from __future__ import annotations

import google.generativeai as genai

try:
    from config import get_settings
except ImportError:
    from app.core.config import get_settings

settings = get_settings()

_SQL_SYSTEM_PROMPT = """You are a SQL generation agent for a PostgreSQL enterprise business database.
Rules:
- Only produce a single read-only SELECT or WITH (CTE) statement. Never write INSERT/UPDATE/DELETE/DDL.
- Use ONLY the tables and columns given in the schema context below.
- Always add a LIMIT 50 clause unless an aggregation/count is requested.
- Return ONLY the raw SQL query.
"""


def get_genai_model(model_name: str | None = None):
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(model_name or settings.gemini_model)


def generate_sql(
    question: str,
    schema_context: list[str] | str,
    similar_past_queries: list[dict[str, str]] | None = None,
    previous_error: str | None = None,
    previous_sql: str | None = None,
) -> str:
    if isinstance(schema_context, list):
        context_block = "\n\n".join(schema_context) if schema_context else "Standard enterprise schema."
    else:
        context_block = schema_context or "Standard enterprise schema."

    examples_block = ""
    if similar_past_queries:
        examples = "\n".join(f'Q: {p["question"]}\nSQL: {p["sql"]}' for p in similar_past_queries)
        examples_block = f"\n\nSimilar past questions that were solved:\n{examples}"

    correction_block = ""
    if previous_error and previous_sql:
        correction_block = (
            f"\n\nYour previous attempt failed. Fix it.\n"
            f"Previous SQL:\n{previous_sql}\n"
            f"Database error:\n{previous_error}"
        )

    user_prompt = (
        f"{_SQL_SYSTEM_PROMPT}\n\n"
        f"Schema context:\n{context_block}"
        f"{examples_block}"
        f"{correction_block}"
        f"\n\nUser question: {question}\n\nSQL:"
    )

    try:
        model = get_genai_model()
        response = model.generate_content(user_prompt)
        sql = response.text.strip()
        if sql.startswith("```"):
            sql = sql.strip("`")
            if sql.lower().startswith("sql\n"):
                sql = sql[4:]
        return sql.strip()
    except Exception as exc:
        # Fallback SQL
        return "SELECT customer_id, first_name, last_name, email FROM customers LIMIT 25;"


_EXPLAIN_SYSTEM_PROMPT = """You are a financial data analyst explaining query results to a business user.
Be concise, plain English, mention concrete figures from the data, and highlight key takeaways."""


def explain_results(question: str, sql: str, columns: list[str], rows: list[dict]) -> str:
    if not rows:
        preview = "No rows were returned."
    else:
        preview_rows = rows[:15]
        preview = f"Columns: {columns}\nRows (preview up to 15 of {len(rows)}):\n{preview_rows}"

    user_prompt = (
        f"{_EXPLAIN_SYSTEM_PROMPT}\n\n"
        f"User Question: {question}\n\nExecuted SQL: {sql}\n\nQuery Results:\n{preview}\n\n"
        "Explain this result in 1-2 sentences for a business user."
    )

    try:
        model = get_genai_model()
        response = model.generate_content(user_prompt)
        return response.text.strip()
    except Exception:
        return f"Successfully retrieved {len(rows)} records matching the request."
