"""
NexusDB Bounded Self-Correcting Reflection Loop
Implements the exact reflection and repair algorithm defined in Section 9.
Captures guard rejections or database errors, refines schema memory context, and repairs SQL up to MAX_RETRIES.
"""

from typing import Any, Callable, Awaitable
from pydantic import BaseModel, Field

from app.core.executor import ExecutionResult


class ErrorReport:
    def __init__(self, summary: str, details: str = "", error_type: str = "ERROR", position: int | None = None):
        self.summary = summary
        self.details = details
        self.error_type = error_type
        self.position = position

    @classmethod
    def from_guard(cls, verdict: Any) -> "ErrorReport":
        return cls(
            summary=verdict.error_message or "Query rejected by schema guard.",
            details=verdict.error_code or "GUARD_REJECTED",
            error_type="GUARD_VALIDATION_ERROR"
        )

    @classmethod
    def from_db_error(cls, error: Exception) -> "ErrorReport":
        err_msg = str(error)
        clean_summary = err_msg.replace("sqlite3.", "").replace("psycopg.", "").strip()
        return cls(
            summary=clean_summary,
            details=repr(error),
            error_type="DATABASE_EXECUTION_ERROR"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "details": self.details,
            "error_type": self.error_type,
            "position": self.position,
        }


class Attempt:
    def __init__(self, attempt_number: int, sql: str, status: str, error: ErrorReport | None = None):
        self.attempt_number = attempt_number
        self.sql = sql
        self.status = status
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "sql": self.sql,
            "status": self.status,
            "error": self.error.to_dict() if self.error else None,
        }


class Outcome:
    def __init__(
        self,
        status: str,
        result: ExecutionResult | None = None,
        attempts: list[Attempt] | None = None,
        sql: str = "",
        user_message: str = "",
    ):
        self.status = status
        self.result = result
        self.attempts = attempts or []
        self.sql = sql
        self.user_message = user_message


def repeats_previous(new_sql: str, attempts: list[Attempt]) -> bool:
    clean_new = " ".join(new_sql.strip().lower().split())
    # Exclude current attempt from comparison
    past_sqls = [" ".join(a.sql.strip().lower().split()) for a in attempts[:-1]]
    return clean_new in past_sqls


def friendly(err: ErrorReport | None) -> str:
    if not err:
        return "Query failed after maximum allowed retry attempts."
    return f"Unable to process query: {err.summary}. Please verify column names or filters."


async def run_reflection(
    question: str,
    ctx: Any,
    llm: Any,
    executor: Any,
    guard: Any,
    memory: Any,
    emit: Callable[..., Awaitable[None]] | None = None,
    max_retries: int = 3,
) -> Outcome:
    attempts: list[Attempt] = []
    err: ErrorReport | None = None

    # Step 1: Draft initial SQL
    draft = await llm.generate_sql(question, ctx)

    # Max executions = 1 initial + max_retries repairs
    for attempt in range(1, max_retries + 2):
        verdict = guard.check(draft.sql, ctx.catalog)
        if verdict.ok:
            try:
                # Read-only execution inside transaction, 5s timeout, 1000 row cap
                result = await executor.run(verdict.sql)
                attempts.append(Attempt(attempt, draft.sql, "ok"))
                return Outcome("SUCCESS", result, attempts, sql=verdict.sql)
            except Exception as e:
                err = ErrorReport.from_db_error(e)
        else:
            err = ErrorReport.from_guard(verdict)

        curr_attempt = Attempt(attempt, draft.sql, "error", err)
        attempts.append(curr_attempt)

        if emit:
            await emit(stage=6, attempt=attempt, sql=draft.sql, error=err.summary)

        # Termination checks: budget exhausted or repeated identical SQL
        if attempt >= (max_retries + 1) or repeats_previous(draft.sql, attempts):
            break

        # Re-retrieve schema memory context with error text feedback
        ctx = await memory.refine(ctx, err)
        draft = await llm.repair_sql(question, ctx, attempts)

    return Outcome(
        status="FAILED",
        result=None,
        attempts=attempts,
        sql=draft.sql,
        user_message=friendly(err),
    )
