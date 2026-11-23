"""
NexusDB Governed Action API Endpoint
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any

from app.deps import get_current_user
from app.governance.rbac import UserSession
from app.governance.actions import get_action_manager

router = APIRouter(prefix="/actions", tags=["Actions"])


class ConfirmActionRequest(BaseModel):
    action_name: str
    parameters: dict[str, Any]
    confirmation_token: str
    idempotency_key: str


@router.post("/confirm")
async def confirm_action(req: ConfirmActionRequest, user: UserSession = Depends(get_current_user)):
    mgr = get_action_manager()
    req_id = f"act_{uuid.uuid4().hex[:12]}"

    try:
        res = mgr.execute_confirmed_action(
            action_name=req.action_name,
            params=req.parameters,
            confirmation_token=req.confirmation_token,
            idempotency_key=req.idempotency_key,
            user=user,
            request_id=req_id,
        )
        return res.model_dump()
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
