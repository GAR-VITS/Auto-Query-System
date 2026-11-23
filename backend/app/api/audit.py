"""
NexusDB Audit Trail API Endpoints
Paged log retrieval and cryptographic SHA-256 chain verification.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.deps import get_current_user
from app.governance.rbac import UserSession
from app.governance.audit import get_audit_manager
from app.db.session import get_db_connection, is_postgres_available
import json

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("")
async def get_audit_log(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: str | None = None,
    user: UserSession = Depends(get_current_user),
):
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        
        # Non-admins see only their own entries
        if user.role != "admin":
            base_query = "SELECT seq, ts, request_id, user_id, role, event_type, status, payload, prev_hash, row_hash FROM audit_log WHERE user_id = ?"
            params = [user.user_id]
        else:
            base_query = "SELECT seq, ts, request_id, user_id, role, event_type, status, payload, prev_hash, row_hash FROM audit_log WHERE 1=1"
            params = []

        if event_type:
            base_query += " AND event_type = ?"
            params.append(event_type)

        base_query += " ORDER BY seq DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur.execute(base_query, tuple(params))
        rows = cur.fetchall()

        entries = []
        for r in rows:
            p_load = json.loads(r[7]) if isinstance(r[7], str) else r[7]
            entries.append({
                "seq": r[0],
                "ts": str(r[1]),
                "request_id": r[2],
                "user_id": r[3],
                "role": r[4],
                "event_type": r[5],
                "status": r[6],
                "payload": p_load,
                "prev_hash": r[8],
                "row_hash": r[9],
            })

        # Count total
        count_q = "SELECT COUNT(*) FROM audit_log" if user.role == "admin" else "SELECT COUNT(*) FROM audit_log WHERE user_id = ?"
        cur.execute(count_q, () if user.role == "admin" else (user.user_id,))
        total_count = cur.fetchone()[0]

        return {
            "entries": entries,
            "total": total_count,
            "limit": limit,
            "offset": offset,
        }


@router.get("/verify")
async def verify_audit_chain(user: UserSession = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators / auditors can verify cryptographic audit chain.")

    mgr = get_audit_manager()
    is_valid, count, message = mgr.verify_chain()
    return {
        "is_valid": is_valid,
        "verified_entries": count,
        "message": message,
    }
