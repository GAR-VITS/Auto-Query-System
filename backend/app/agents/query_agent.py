"""
NexusDB Query Agent
Coordinates semantic schema slice retrieval and the self-correcting reflection loop.
"""

from typing import Callable, Awaitable, Any
from app.agents.contracts import QueryRequest, QueryResult
from app.core.reflection import run_reflection, Outcome
from app.core.sql_guard import get_sql_guard
from app.core.executor import SqlExecutor
from app.memory.store import get_schema_memory
from app.llm.base import LLMClient


class QueryAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.memory = get_schema_memory()
        self.guard = get_sql_guard()
        self.executor = SqlExecutor(role="nexus_reader")

    async def execute(
        self,
        request: QueryRequest,
        emit_stage: Callable[..., Awaitable[None]] | None = None,
    ) -> QueryResult:
        # Step 1: Retrieve schema context from ChromaDB
        if emit_stage:
            await emit_stage(stage=4, name="Schema retrieval (ChromaDB)", status="start", ms=0)

        context = self.memory.retrieve(request.question)

        if emit_stage:
            await emit_stage(
                stage=4,
                name="Schema retrieval (ChromaDB)",
                status="done",
                ms=15,
                detail=f"Retrieved {len(context.retrieved_tables)} tables ({context.context_saved_pct}% prompt context saved)"
            )

        # Step 2 & 3: Run Reflection loop (drafting + validation + retries)
        if emit_stage:
            await emit_stage(stage=5, name="SQL drafting (LLM)", status="start", ms=0)
            await emit_stage(stage=5, name="SQL drafting (LLM)", status="done", ms=45)
            await emit_stage(stage=6, name="Reflection loop", status="start", ms=0)

        outcome: Outcome = await run_reflection(
            question=request.question,
            ctx=context,
            llm=self.llm,
            executor=self.executor,
            guard=self.guard,
            memory=self.memory,
            emit=emit_stage,
            max_retries=3,
        )

        attempts_data = [a.to_dict() for a in outcome.attempts]

        if outcome.status == "SUCCESS" and outcome.result:
            if emit_stage:
                repairs = len(outcome.attempts) - 1
                detail_msg = f"Validated & executed successfully ({repairs} repairs)" if repairs > 0 else "Validated & executed on attempt 1"
                await emit_stage(stage=6, name="Reflection loop", status="done", ms=50, detail=detail_msg)

            return QueryResult(
                sql=outcome.sql,
                columns=outcome.result.columns,
                rows=outcome.result.rows,
                row_count=outcome.result.row_count,
                truncated=outcome.result.truncated,
                attempts=attempts_data,
                interpretation=f"Read as query against tables {', '.join(context.retrieved_tables[:4])}",
            )
        else:
            if emit_stage:
                await emit_stage(stage=6, name="Reflection loop", status="error", ms=50, detail=outcome.user_message)

            raise RuntimeError(outcome.user_message)
