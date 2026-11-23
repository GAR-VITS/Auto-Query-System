"""
NexusDB 11-Stage Pipeline Orchestration
Executes the full conversational and governed write-back lifecycle:
Stages 1..11, emitting live SSE frames to the client.
"""

import time
import json
import uuid
from typing import AsyncGenerator, Any

from app.config import get_settings
from app.agents.contracts import QueryRequest
from app.agents.crew import Orchestrator
from app.llm.gemini import get_llm_client
from app.governance.rbac import UserSession
from app.governance.audit import get_audit_manager
from app.governance.actions import get_action_manager

settings = get_settings()


class PipelineEvent:
    def __init__(self, event_type: str, data: dict[str, Any]):
        self.event_type = event_type
        self.data = data

    def to_sse(self) -> str:
        payload = json.dumps(self.data, default=str)
        return f"event: {self.event_type}\ndata: {payload}\n\n"


async def execute_query_pipeline(
    question: str,
    user: UserSession,
    request_id: str | None = None,
    is_voice: bool = False,
) -> AsyncGenerator[str, None]:
    """Executes the 11 stages and yields formatted Server-Sent Event (SSE) frames."""
    start_time = time.time()
    req_id = request_id or f"req_{uuid.uuid4().hex[:12]}"
    audit = get_audit_manager()
    action_mgr = get_action_manager()
    llm = get_llm_client()
    orchestrator = Orchestrator(llm)

    # Stage 1: Query received
    yield PipelineEvent("stage", {
        "n": 1,
        "name": "Query received (text or voice)",
        "status": "done",
        "ms": round((time.time() - start_time) * 1000, 1),
        "detail": f"Input mode: {'Voice (Web Speech API)' if is_voice else 'Text input'}"
    }).to_sse()

    # Stage 2: Client transcription (passed through)
    yield PipelineEvent("stage", {
        "n": 2,
        "name": "Transcription on the client",
        "status": "done",
        "ms": round((time.time() - start_time) * 1000, 1),
        "detail": "Verified client-side utterance transcript" if is_voice else "Standard text payload"
    }).to_sse()

    # Stage 3: Gateway and token auth
    yield PipelineEvent("stage", {
        "n": 3,
        "name": "Gateway and token auth",
        "status": "done",
        "ms": round((time.time() - start_time) * 1000, 1),
        "detail": f"Authenticated user '{user.username}' with role '{user.role}'"
    }).to_sse()

    # Callback helper to emit stage events from query agent / reflection loop
    stage_events: list[PipelineEvent] = []

    async def emit_stage_event(stage: int, name: str = "", status: str = "done", ms: float = 0, detail: str = "", attempt: int | None = None, sql: str | None = None, error: str | None = None):
        nonlocal stage_events
        data = {"n": stage, "name": name, "status": status, "ms": ms, "detail": detail}
        if attempt is not None:
            data["attempt"] = attempt
        if sql is not None:
            data["sql"] = sql
        if error is not None:
            data["error"] = error

        stage_events.append(PipelineEvent("stage", data))
        if attempt is not None and error is not None:
            stage_events.append(PipelineEvent("attempt", {"n": attempt, "sql": sql, "error": error}))

    # Classify user intent
    intent_res = await llm.classify_intent(question)

    if intent_res.intent == "clarify":
        # Clarification needed
        yield PipelineEvent("clarify", {"question": intent_res.clarify_question}).to_sse()
        yield PipelineEvent("done", {"request_id": req_id, "total_ms": round((time.time() - start_time) * 1000, 1)}).to_sse()
        return

    elif intent_res.intent == "action":
        # Stage 9: Action module (RBAC) preview
        yield PipelineEvent("stage", {
            "n": 9,
            "name": "Action module (RBAC)",
            "status": "start",
            "ms": round((time.time() - start_time) * 1000, 1),
            "detail": f"Evaluating pre-authorized action '{intent_res.action_name}'"
        }).to_sse()

        try:
            preview = action_mgr.preview_action(
                action_name=intent_res.action_name or "SET_ACCOUNT_STATUS",
                params=intent_res.parameters,
                user=user,
                request_id=req_id,
            )
            yield PipelineEvent("stage", {
                "n": 9,
                "name": "Action module (RBAC)",
                "status": "done",
                "ms": round((time.time() - start_time) * 1000, 1),
                "detail": f"Action authorized. Generated 2-minute single-use confirmation token."
            }).to_sse()

            yield PipelineEvent("action_proposal", preview.model_dump()).to_sse()

            # Stage 10: Audit trail write
            audit_ev = audit.append_event(
                request_id=req_id,
                user_id=user.user_id,
                role=user.role,
                event_type="ACTION_PROPOSED",
                status="PROPOSED",
                payload={"action": intent_res.action_name, "preview": preview.model_dump()}
            )
            yield PipelineEvent("stage", {
                "n": 10,
                "name": "Audit trail write",
                "status": "done",
                "ms": round((time.time() - start_time) * 1000, 1),
                "detail": f"Appended immutable audit block #{audit_ev.seq}"
            }).to_sse()

            # Stage 11: Delivery to client
            yield PipelineEvent("stage", {
                "n": 11,
                "name": "Delivery to client",
                "status": "done",
                "ms": round((time.time() - start_time) * 1000, 1),
                "detail": "Streamed action preview and confirmation card"
            }).to_sse()

            yield PipelineEvent("done", {"request_id": req_id, "total_ms": round((time.time() - start_time) * 1000, 1)}).to_sse()
            return

        except Exception as e:
            yield PipelineEvent("stage", {
                "n": 9,
                "name": "Action module (RBAC)",
                "status": "error",
                "ms": round((time.time() - start_time) * 1000, 1),
                "detail": str(e)
            }).to_sse()
            yield PipelineEvent("error", {"message": str(e)}).to_sse()
            yield PipelineEvent("done", {"request_id": req_id, "total_ms": round((time.time() - start_time) * 1000, 1)}).to_sse()
            return

    # Standard Read-Only Query Flow (Stages 4 through 8)
    req = QueryRequest(
        question=question,
        user_id=user.user_id,
        role=user.role,
        request_id=req_id,
        branch_id=user.branch_id,
    )

    try:
        query_res, analysis_res, viz_spec = await orchestrator.run(
            request=req,
            emit_stage=emit_stage_event,
            timeout_seconds=30.0,
        )

        # Flush stages 4, 5, 6, 7, 8 captured during orchestrator run
        for ev in stage_events:
            yield ev.to_sse()

        # Emit query result table
        yield PipelineEvent("result", {
            "sql": query_res.sql,
            "columns": query_res.columns,
            "rows": query_res.rows,
            "row_count": query_res.row_count,
            "truncated": query_res.truncated,
            "attempts": query_res.attempts,
            "interpretation": query_res.interpretation,
        }).to_sse()

        # Emit analysis insight
        yield PipelineEvent("analysis", {
            "stats": analysis_res.stats,
            "insight_text": analysis_res.insight_text,
            "read_as": analysis_res.read_as,
            "flags": analysis_res.flags,
        }).to_sse()

        # Emit chart specification
        yield PipelineEvent("viz", viz_spec.model_dump()).to_sse()

        # Stage 10: Audit trail write (only counts and query metadata - NEVER raw data)
        audit_ev = audit.append_event(
            request_id=req_id,
            user_id=user.user_id,
            role=user.role,
            event_type="QUERY",
            status="SUCCESS",
            payload={
                "question": question,
                "sql": query_res.sql,
                "row_count": query_res.row_count,
                "attempts_count": len(query_res.attempts),
                "latency_ms": round((time.time() - start_time) * 1000, 1),
            }
        )
        yield PipelineEvent("stage", {
            "n": 10,
            "name": "Audit trail write",
            "status": "done",
            "ms": round((time.time() - start_time) * 1000, 1),
            "detail": f"Recorded query audit entry #{audit_ev.seq}"
        }).to_sse()

        # Stage 11: Delivery to client
        yield PipelineEvent("stage", {
            "n": 11,
            "name": "Delivery to client",
            "status": "done",
            "ms": round((time.time() - start_time) * 1000, 1),
            "detail": f"Delivered {query_res.row_count} rows and visualization"
        }).to_sse()

        yield PipelineEvent("done", {
            "request_id": req_id,
            "total_ms": round((time.time() - start_time) * 1000, 1),
            "repairs": len(query_res.attempts) - 1,
            "row_count": query_res.row_count,
        }).to_sse()

    except Exception as e:
        for ev in stage_events:
            yield ev.to_sse()

        err_msg = str(e)
        audit.append_event(
            request_id=req_id,
            user_id=user.user_id,
            role=user.role,
            event_type="FAILED",
            status="FAILED",
            payload={"question": question, "error": err_msg}
        )
        yield PipelineEvent("error", {"message": err_msg}).to_sse()
        yield PipelineEvent("done", {
            "request_id": req_id,
            "total_ms": round((time.time() - start_time) * 1000, 1),
            "status": "FAILED"
        }).to_sse()
