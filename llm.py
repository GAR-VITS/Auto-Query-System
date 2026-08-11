"""
Thin wrapper around Gemini 1.5 Pro via LangChain.

Two jobs, kept as separate prompts (separate concerns = easier to tune):
1. generate_sql(): natural language + retrieved schema context -> SQL
2. explain_results(): SQL + result rows -> plain English answer
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings

settings = get_settings()

_llm: ChatGoogleGenerativeAI | None = None


def get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0,  # deterministic SQL generation
        )
    return _llm


_SQL_SYSTEM_PROMPT = """You are a SQL generation agent for a PostgreSQL business database.
Rules:
- Only ever produce a single SELECT or WITH (CTE) statement. Never write INSERT/UPDATE/DELETE/DDL.
- Use ONLY the tables and columns given in the schema context below. Never invent columns.
- Always add a LIMIT clause if the user didn't ask for an aggregate/count.
- Return ONLY the raw SQL, no markdown fences, no commentary.
"""


def generate_sql(
    question: str,
    schema_context: list[str],
    similar_past_queries: list[dict[str, str]] | None = None,
    previous_error: str | None = None,
    previous_sql: str | None = None,
) -> str:
    """
    Builds the prompt from retrieved context and, on retries, the previous
    failed SQL + the Postgres error message — this is the self-correction loop.
    """
    context_block = "\n\n".join(schema_context) if schema_context else "No schema context found."

    examples_block = ""
    if similar_past_queries:
        examples = "\n".join(
            f'Q: {p["question"]}\nSQL: {p["sql"]}' for p in similar_past_queries
        )
        examples_block = f"\n\nSimilar past questions that were solved successfully:\n{examples}"

    correction_block = ""
    if previous_error and previous_sql:
        correction_block = (
            f"\n\nYour previous attempt failed. Fix it.\n"
            f"Previous SQL:\n{previous_sql}\n"
            f"Database error:\n{previous_error}"
        )

    user_prompt = (
        f"Schema context (nearest tables to this question):\n{context_block}"
        f"{examples_block}"
        f"{correction_block}"
        f"\n\nUser question: {question}\n\nSQL:"
    )

    response = get_llm().invoke(
        [SystemMessage(content=_SQL_SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
    )
    sql = response.content.strip()
    # Strip accidental markdown fences even though the prompt forbids them.
    if sql.startswith("```"):
        sql = sql.strip("`")
        sql = sql.replace("sql\n", "", 1) if sql.lower().startswith("sql\n") else sql
    return sql.strip()


_EXPLAIN_SYSTEM_PROMPT = """You are a data analyst explaining query results to a non-technical
business user. Be concise, use plain English, mention concrete numbers from the data,
and never mention SQL, tables, or column names literally unless the user used those words."""


def explain_results(question: str, sql: str, columns: list[str], rows: list[dict]) -> str:
    if not rows:
        preview = "No rows were returned."
    else:
        preview_rows = rows[:20]
        preview = f"Columns: {columns}\nRows (showing up to 20 of {len(rows)}):\n{preview_rows}"

    user_prompt = (
        f"Original question: {question}\n\nQuery result:\n{preview}\n\n"
        "Explain this result in plain English, directly answering the question."
    )
    response = get_llm().invoke(
        [SystemMessage(content=_EXPLAIN_SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
    )
    return response.content.strip()
