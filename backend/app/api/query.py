"""
NexusDB Query Streaming API Endpoint
POST /query/stream -> Returns text/event-stream SSE frames of 11 pipeline stages.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.deps import get_current_user
from app.governance.rbac import UserSession
from app.core.pipeline import execute_query_pipeline

router = APIRouter(tags=["Query"])


class QueryStreamRequest(BaseModel):
    question: str
    request_id: str | None = None
    is_voice: bool = False


@router.post("/query/stream")
async def stream_query(req: QueryStreamRequest, user: UserSession = Depends(get_current_user)):
    return StreamingResponse(
        execute_query_pipeline(
            question=req.question,
            user=user,
            request_id=req.request_id,
            is_voice=req.is_voice,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
