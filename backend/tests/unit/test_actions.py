"""
Unit Tests for Governed Action Catalogue (Section 11 Specification)
Tests parameter validation, branch scope, and preconditions.
"""

import pytest
from app.governance.actions import ActionManager
from app.governance.rbac import UserSession
from app.db.session import get_db_connection

@pytest.fixture
def action_mgr():
    return ActionManager()

def test_action_branch_officer_own_branch(action_mgr):
    # Find an account belonging to branch 1 that is ACTIVE
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM accounts WHERE branch_id = 1 AND status = 'ACTIVE' LIMIT 1")
        row = cur.fetchone()
        acc_id = row[0] if row else 1

    officer = UserSession(user_id="officer", username="officer1", role="branch_officer", branch_id=1)
    preview = action_mgr.preview_action(
        action_name="SET_ACCOUNT_STATUS",
        params={"account_id": acc_id, "new_status": "HOLD", "reason": "Suspicious ATM withdrawal"},
        user=officer,
        request_id="req_test_01",
    )
    assert preview.action_name == "SET_ACCOUNT_STATUS"
    assert preview.after_state["status"] == "HOLD"
    assert preview.confirmation_token is not None

def test_action_branch_officer_foreign_branch_denied(action_mgr):
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        cur.execute("SELECT account_id, branch_id, status FROM accounts WHERE branch_id != 99 LIMIT 1")
        acc_id, branch_id, curr_status = cur.fetchone()
    target_status = "HOLD" if curr_status != "HOLD" else "ACTIVE"

    foreign_officer = UserSession(user_id="officer_foreign", username="officer_foreign", role="branch_officer", branch_id=99)
    with pytest.raises(PermissionError) as exc_info:
        action_mgr.preview_action(
            action_name="SET_ACCOUNT_STATUS",
            params={"account_id": acc_id, "new_status": target_status, "reason": "Foreign branch attempt"},
            user=foreign_officer,
            request_id="req_test_02",
        )
    assert "scope violation" in str(exc_info.value).lower()

def test_action_viewer_denied(action_mgr):
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        cur.execute("SELECT account_id, status FROM accounts LIMIT 1")
        acc_id, curr_status = cur.fetchone()
    target_status = "HOLD" if curr_status != "HOLD" else "ACTIVE"

    viewer = UserSession(user_id="viewer", username="viewer1", role="viewer")
    with pytest.raises(PermissionError) as exc_info:
        action_mgr.preview_action(
            action_name="SET_ACCOUNT_STATUS",
            params={"account_id": acc_id, "new_status": target_status, "reason": "Unauthorized attempt"},
            user=viewer,
            request_id="req_test_03",
        )
    assert "cannot update account status" in str(exc_info.value).lower()

def test_action_precondition_same_status(action_mgr):
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        cur.execute("SELECT account_id, status FROM accounts LIMIT 1")
        acc_id, curr_status = cur.fetchone()

    manager = UserSession(user_id="manager", username="manager1", role="credit_manager")
    with pytest.raises(ValueError) as exc_info:
        action_mgr.preview_action(
            action_name="SET_ACCOUNT_STATUS",
            params={"account_id": acc_id, "new_status": curr_status, "reason": "Already in this status"},
            user=manager,
            request_id="req_test_04",
        )
    assert f"already in {curr_status.lower()} status" in str(exc_info.value).lower()

def test_action_confirm_execution_and_idempotency(action_mgr):
    manager = UserSession(user_id="manager", username="manager1", role="credit_manager")
    
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        cur.execute("SELECT account_id, status FROM accounts WHERE status = 'ACTIVE' LIMIT 1")
        row = cur.fetchone()
        acc_id = row[0] if row else 2

    preview = action_mgr.preview_action(
        action_name="SET_ACCOUNT_STATUS",
        params={"account_id": acc_id, "new_status": "HOLD", "reason": "Testing action confirm"},
        user=manager,
        request_id="req_test_05",
    )

    # First execution succeeds
    res1 = action_mgr.execute_confirmed_action(
        action_name="SET_ACCOUNT_STATUS",
        params={"account_id": acc_id, "new_status": "HOLD", "reason": "Testing action confirm"},
        confirmation_token=preview.confirmation_token,
        idempotency_key="idemp_key_999",
        user=manager,
        request_id="req_test_05_exec",
    )
    assert res1.success
    assert res1.audit_seq > 0

    # Second execution with same idempotency key (simulating double click) returns idempotent success without duplicate execution
    res2 = action_mgr.execute_confirmed_action(
        action_name="SET_ACCOUNT_STATUS",
        params={"account_id": acc_id, "new_status": "HOLD", "reason": "Testing action confirm"},
        confirmation_token=preview.confirmation_token,
        idempotency_key="idemp_key_999",
        user=manager,
        request_id="req_test_05_exec_dup",
    )
    assert res2.success
    assert res2.audit_seq == res1.audit_seq
