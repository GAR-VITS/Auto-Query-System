"""
Unit Tests for Governed Action Catalogue (Section 11 Specification)
Tests parameter validation, branch scope, and preconditions.
"""

import pytest
from app.governance.actions import ActionManager
from app.governance.rbac import UserSession

@pytest.fixture
def action_mgr():
    return ActionManager()

def test_action_branch_officer_own_branch(action_mgr):
    # Find an account belonging to branch 1
    from app.db.session import get_db_connection
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM accounts WHERE branch_id = 1 AND status = 'ACTIVE' LIMIT 1")
        acc_id = cur.fetchone()[0]

    # Officer in branch 1 updating their own branch account to HOLD
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
    # Officer in branch 99 attempting to update account in branch 1
    foreign_officer = UserSession(user_id="officer_foreign", username="officer_foreign", role="branch_officer", branch_id=99)
    with pytest.raises(PermissionError) as exc_info:
        action_mgr.preview_action(
            action_name="SET_ACCOUNT_STATUS",
            params={"account_id": 1, "new_status": "HOLD", "reason": "Foreign branch attempt"},
            user=foreign_officer,
            request_id="req_test_02",
        )
    assert "scope violation" in str(exc_info.value).lower()

def test_action_viewer_denied(action_mgr):
    viewer = UserSession(user_id="viewer", username="viewer1", role="viewer")
    with pytest.raises(PermissionError) as exc_info:
        action_mgr.preview_action(
            action_name="SET_ACCOUNT_STATUS",
            params={"account_id": 1, "new_status": "HOLD", "reason": "Unauthorized attempt"},
            user=viewer,
            request_id="req_test_03",
        )
    assert "cannot update account status" in str(exc_info.value).lower()

def test_action_precondition_same_status(action_mgr):
    # Account 1 is already in ACTIVE status
    manager = UserSession(user_id="manager", username="manager1", role="credit_manager")
    with pytest.raises(ValueError) as exc_info:
        action_mgr.preview_action(
            action_name="SET_ACCOUNT_STATUS",
            params={"account_id": 1, "new_status": "ACTIVE", "reason": "Already active"},
            user=manager,
            request_id="req_test_04",
        )
    assert "already in active status" in str(exc_info.value).lower()

def test_action_confirm_execution_and_idempotency(action_mgr):
    manager = UserSession(user_id="manager", username="manager1", role="credit_manager")
    
    # Dynamically find an account that is ACTIVE to put on HOLD
    from app.db.session import get_db_connection
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        cur.execute("SELECT account_id FROM accounts WHERE status = 'ACTIVE' LIMIT 1")
        acc_id = cur.fetchone()[0]

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
        request_id="req_test_05_exec2",
    )
    assert res2.success
    assert "already applied" in res2.message.lower()
