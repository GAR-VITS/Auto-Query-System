"""
Unit Tests for Self-Correcting Reflection Loop (Section 16 Specification)
Tests fault injection with an LLM that fails 0, 1, 2, 3, and 4 times:
- asserts final outcome
- asserts attempts never exceed 4
- asserts that a repeated identical SQL stops the loop early
"""

import asyncio
import pytest
from app.core.reflection import run_reflection
from app.core.sql_guard import SqlGuard
from app.core.executor import SqlExecutor
from app.memory.store import get_schema_memory
from app.llm.base import GeneratedSql


class FaultInjectingLLM:
    """Fake LLM that produces faulty SQL queries for a configurable number of failures."""
    def __init__(self, failure_count: int, repeat_sql: bool = False):
        self.failure_count = failure_count
        self.repeat_sql = repeat_sql
        self.call_count = 0

    async def generate_sql(self, question: str, context: any) -> GeneratedSql:
        self.call_count += 1
        if self.call_count <= self.failure_count:
            return GeneratedSql(
                sql="SELECT c.non_existent_column FROM bank.customers c",
                rationale="Fault injected bad column.",
            )
        return GeneratedSql(
            sql="SELECT c.customer_id, c.full_name FROM bank.customers c LIMIT 5",
            rationale="Correct query.",
        )

    async def repair_sql(self, question: str, context: any, attempts: list) -> GeneratedSql:
        self.call_count += 1
        if self.repeat_sql:
            # Repeat the exact same SQL to test early exit
            return GeneratedSql(
                sql="SELECT c.non_existent_column FROM bank.customers c",
                rationale="Repeated faulty query.",
            )

        if self.call_count <= self.failure_count:
            return GeneratedSql(
                sql=f"SELECT c.bad_column_{self.call_count} FROM bank.customers c",
                rationale=f"Fault attempt {self.call_count}.",
            )
        return GeneratedSql(
            sql="SELECT c.customer_id, c.full_name FROM bank.customers c LIMIT 5",
            rationale="Repaired query after failures.",
        )


@pytest.fixture
def test_setup():
    guard = SqlGuard()
    executor = SqlExecutor(role="nexus_reader")
    memory = get_schema_memory()
    ctx = memory.retrieve("Show customer names")
    return guard, executor, memory, ctx


def test_reflection_zero_failures(test_setup):
    guard, executor, memory, ctx = test_setup
    llm = FaultInjectingLLM(failure_count=0)
    outcome = asyncio.run(run_reflection("Show customer names", ctx, llm, executor, guard, memory, max_retries=3))

    assert outcome.status == "SUCCESS"
    assert len(outcome.attempts) == 1
    assert outcome.result is not None
    assert outcome.result.row_count > 0


def test_reflection_one_failure(test_setup):
    guard, executor, memory, ctx = test_setup
    llm = FaultInjectingLLM(failure_count=1)
    outcome = asyncio.run(run_reflection("Show customer names", ctx, llm, executor, guard, memory, max_retries=3))

    assert outcome.status == "SUCCESS"
    assert len(outcome.attempts) == 2
    assert outcome.attempts[0].status == "error"
    assert outcome.attempts[1].status == "ok"


def test_reflection_two_failures(test_setup):
    guard, executor, memory, ctx = test_setup
    llm = FaultInjectingLLM(failure_count=2)
    outcome = asyncio.run(run_reflection("Show customer names", ctx, llm, executor, guard, memory, max_retries=3))

    assert outcome.status == "SUCCESS"
    assert len(outcome.attempts) == 3
    assert outcome.attempts[0].status == "error"
    assert outcome.attempts[1].status == "error"
    assert outcome.attempts[2].status == "ok"


def test_reflection_three_failures(test_setup):
    guard, executor, memory, ctx = test_setup
    llm = FaultInjectingLLM(failure_count=3)
    outcome = asyncio.run(run_reflection("Show customer names", ctx, llm, executor, guard, memory, max_retries=3))

    assert outcome.status == "SUCCESS"
    assert len(outcome.attempts) == 4
    assert outcome.attempts[3].status == "ok"


def test_reflection_four_failures_exhaustion(test_setup):
    guard, executor, memory, ctx = test_setup
    # Fails 4 times: should exhaust retry budget (1 initial + 3 repairs = 4 attempts total)
    llm = FaultInjectingLLM(failure_count=4)
    outcome = asyncio.run(run_reflection("Show customer names", ctx, llm, executor, guard, memory, max_retries=3))

    assert outcome.status == "FAILED"
    assert len(outcome.attempts) == 4
    assert outcome.result is None
    assert "Unable to process query" in outcome.user_message


def test_reflection_repeated_sql_stops_early(test_setup):
    guard, executor, memory, ctx = test_setup
    # LLM repeats the exact same failing SQL
    llm = FaultInjectingLLM(failure_count=5, repeat_sql=True)
    outcome = asyncio.run(run_reflection("Show customer names", ctx, llm, executor, guard, memory, max_retries=3))

    assert outcome.status == "FAILED"
    # Should stop on attempt 2 as soon as repetition is detected, without wasting remaining attempts!
    assert len(outcome.attempts) == 2
