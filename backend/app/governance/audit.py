"""
NexusDB Cryptographic Hash-Chained Audit Trail
Implements tamper-evident append-only audit logging and cryptographic verification.
row_hash = SHA256(prev_hash + canonical_json(seq, ts, request_id, user_id, event_type, status, payload))
"""

import hashlib
import json
import sqlite3
from typing import Any
from datetime import datetime, timezone
from sqlalchemy import text

from app.config import get_settings
from app.db.session import is_postgres_available, get_db_connection

settings = get_settings()

GENESIS_PREV_HASH = "0" * 64


def canonical_json(data: Any) -> str:
    """Produces deterministic, canonical JSON with sorted keys and no whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


class AuditEvent:
    def __init__(
        self,
        seq: int,
        ts: str,
        request_id: str,
        user_id: str,
        role: str,
        event_type: str,
        status: str,
        payload: dict[str, Any],
        prev_hash: str,
        row_hash: str,
    ):
        self.seq = seq
        self.ts = ts
        self.request_id = request_id
        self.user_id = user_id
        self.role = role
        self.event_type = event_type
        self.status = status
        self.payload = payload
        self.prev_hash = prev_hash
        self.row_hash = row_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "ts": self.ts,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "role": self.role,
            "event_type": self.event_type,
            "status": self.status,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "row_hash": self.row_hash,
        }


def compute_row_hash(
    prev_hash: str,
    seq: int,
    ts: str,
    request_id: str,
    user_id: str,
    event_type: str,
    status: str,
    payload: Any,
) -> str:
    payload_dict = payload if isinstance(payload, dict) else (json.loads(payload) if isinstance(payload, str) and payload.startswith("{") else payload)
    data = {
        "seq": int(seq),
        "ts": str(ts),
        "request_id": str(request_id),
        "user_id": str(user_id),
        "event_type": str(event_type),
        "status": str(status),
        "payload": payload_dict,
    }
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    hasher = hashlib.sha256()
    hasher.update((prev_hash + canonical).encode("utf-8"))
    return hasher.hexdigest()


class AuditManager:
    def append_event(
        self,
        request_id: str,
        user_id: str,
        role: str,
        event_type: str,
        status: str,
        payload: dict[str, Any],
    ) -> AuditEvent:
        """Appends an event to the hash-chained audit log with serialized locking."""
        with get_db_connection("nexus_writer") as conn:
            cur = conn.cursor() if hasattr(conn, "cursor") else conn

            # Fetch the latest audit entry to link the hash chain
            if is_postgres_available():
                # Advisory lock to serialize concurrent appends
                cur.execute(text("SELECT pg_advisory_xact_lock(987654321)"))
                res = cur.execute(text("SELECT seq, row_hash FROM audit.log ORDER BY seq DESC LIMIT 1")).fetchone()
            else:
                res = cur.execute("SELECT seq, row_hash FROM audit_log ORDER BY seq DESC LIMIT 1").fetchone()

            if res:
                last_seq, last_hash = res[0], res[1]
                new_seq = last_seq + 1
                prev_hash = last_hash
            else:
                new_seq = 1
                prev_hash = GENESIS_PREV_HASH

            now_iso = datetime.now(timezone.utc).isoformat()
            row_hash = compute_row_hash(
                prev_hash=prev_hash,
                seq=new_seq,
                ts=now_iso,
                request_id=request_id,
                user_id=user_id,
                event_type=event_type,
                status=status,
                payload=payload,
            )

            payload_json = json.dumps(payload, default=str)

            if is_postgres_available():
                cur.execute(
                    text("""
                    INSERT INTO audit.log (seq, ts, request_id, user_id, role, event_type, status, payload, prev_hash, row_hash)
                    VALUES (:seq, :ts, :req_id, :uid, :role, :ev, :st, :payload, :prev, :curr)
                    """),
                    {
                        "seq": new_seq, "ts": now_iso, "req_id": request_id, "uid": user_id,
                        "role": role, "ev": event_type, "st": status, "payload": payload_json,
                        "prev": prev_hash, "curr": row_hash
                    }
                )
            else:
                cur.execute("""
                INSERT INTO audit_log (seq, ts, request_id, user_id, role, event_type, status, payload, prev_hash, row_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (new_seq, now_iso, request_id, user_id, role, event_type, status, payload_json, prev_hash, row_hash))

            return AuditEvent(
                seq=new_seq,
                ts=now_iso,
                request_id=request_id,
                user_id=user_id,
                role=role,
                event_type=event_type,
                status=status,
                payload=payload,
                prev_hash=prev_hash,
                row_hash=row_hash,
            )

    def verify_chain(self) -> tuple[bool, int, str]:
        """
        Walks the entire audit log, recomputing every SHA-256 hash in sequence.
        Returns (is_valid, count_verified, message).
        """
        with get_db_connection("nexus_reader") as conn:
            cur = conn.cursor() if hasattr(conn, "cursor") else conn
            query = "SELECT seq, ts, request_id, user_id, role, event_type, status, payload, prev_hash, row_hash FROM audit_log ORDER BY seq ASC"
            if is_postgres_available():
                query = "SELECT seq, ts, request_id, user_id, role, event_type, status, payload, prev_hash, row_hash FROM audit.log ORDER BY seq ASC"

            cur.execute(text(query) if is_postgres_available() else query)
            rows = cur.fetchall()

            if not rows:
                return True, 0, "Audit log is empty."

            expected_prev_hash = GENESIS_PREV_HASH
            for row in rows:
                seq, ts, req_id, uid, role, ev, st, payload_raw, prev_h, row_h = row
                
                # Check link to previous hash
                if prev_h != expected_prev_hash:
                    return False, seq, f"Hash chain broken at seq {seq}: prev_hash mismatch."

                # Parse payload
                payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw

                # Recompute row hash
                recomputed = compute_row_hash(
                    prev_hash=prev_h,
                    seq=seq,
                    ts=str(ts),
                    request_id=req_id,
                    user_id=uid,
                    event_type=ev,
                    status=st,
                    payload=payload,
                )

                if recomputed != row_h:
                    return False, seq, f"Data tampering detected at entry {seq}: hash mismatch."

                expected_prev_hash = row_h

            return True, len(rows), f"Chain intact, {len(rows)} entries verified."


_audit_manager: AuditManager | None = None


def get_audit_manager() -> AuditManager:
    global _audit_manager
    if _audit_manager is None:
        _audit_manager = AuditManager()
    return _audit_manager
