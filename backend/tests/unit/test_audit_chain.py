"""
Unit Tests for Cryptographic Hash-Chained Audit Trail (Section 13 Specification)
Tests sequential append, verify_chain(), and mathematical tamper detection.
"""

import json
import sqlite3
import pytest
from app.governance.audit import get_audit_manager
from app.db.session import get_sqlite_path


def test_audit_append_and_verify():
    mgr = get_audit_manager()

    ev1 = mgr.append_event(
        request_id="test_req_001",
        user_id="user_1",
        role="viewer",
        event_type="QUERY",
        status="SUCCESS",
        payload={"query": "SELECT 1", "rows": 1}
    )
    assert ev1.seq > 0
    assert len(ev1.row_hash) == 64

    ev2 = mgr.append_event(
        request_id="test_req_002",
        user_id="user_2",
        role="branch_officer",
        event_type="ACTION_PROPOSED",
        status="PROPOSED",
        payload={"action": "SET_ACCOUNT_STATUS"}
    )
    assert ev2.prev_hash == ev1.row_hash

    is_valid, count, msg = mgr.verify_chain()
    assert is_valid
    assert count >= 2
    assert "Chain intact" in msg


def test_audit_tamper_detection():
    mgr = get_audit_manager()
    db_file = get_sqlite_path()

    # Append fresh event to test chain
    ev_a = mgr.append_event("req_tamper_test", "u1", "viewer", "QUERY", "SUCCESS", {"sample_field": 42})

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT payload, row_hash FROM audit_log WHERE seq = ?", (ev_a.seq,))
    orig_payload, orig_row_hash = cur.fetchone()

    try:
        # Malicious modification: tamper with payload directly
        cur.execute("DROP TRIGGER IF EXISTS trg_audit_no_update;")
        cur.execute("UPDATE audit_log SET payload = '{\"tampered\": true}' WHERE seq = ?", (ev_a.seq,))
        conn.commit()

        # verify_chain() MUST detect the tampering!
        is_valid, broken_seq, msg = mgr.verify_chain()
        assert not is_valid
        assert broken_seq == ev_a.seq
        assert "tampering detected" in msg.lower() or "mismatch" in msg.lower()

    finally:
        # Restore original payload and row_hash and recreate trigger
        cur.execute("UPDATE audit_log SET payload = ?, row_hash = ? WHERE seq = ?", (orig_payload, orig_row_hash, ev_a.seq))
        cur.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_audit_no_update
        BEFORE UPDATE ON audit_log
        BEGIN
            SELECT RAISE(FAIL, 'audit.log is strictly append-only. UPDATE prohibited.');
        END;
        """)
        conn.commit()
        conn.close()
