"""
Unit Tests for RBAC Matrix (Section 12 Specification)
Parametrized test over every single role and permission in Section 12.
"""

import pytest
from app.governance.rbac import UserSession, PERMISSIONS_MATRIX

ROLES = ["viewer", "branch_officer", "credit_manager", "admin"]
PERMISSIONS = [
    "query:run",
    "schema:view",
    "action:set_account_status",
    "action:set_risk_flag",
    "action:clear_risk_flag",
    "audit:read_own",
    "audit:read_all",
    "audit:verify",
    "user:manage",
]


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("permission", PERMISSIONS)
def test_rbac_permission_matrix(role, permission):
    user = UserSession(user_id=f"test_{role}", username=f"user_{role}", role=role, branch_id=1)
    expected_rule = PERMISSIONS_MATRIX[permission][role]

    if expected_rule is True:
        assert user.has_permission(permission), f"Role {role} should have permission {permission}"
    elif expected_rule is False:
        assert not user.has_permission(permission), f"Role {role} should NOT have permission {permission}"
    elif expected_rule == "limited":
        # Branch officer limited permission
        assert permission == "action:set_account_status"
        # Can update own branch to ACTIVE or HOLD
        can_do, msg = user.can_update_account(target_account_branch_id=1, new_status="HOLD")
        assert can_do
        # Cannot update foreign branch
        can_foreign, msg2 = user.can_update_account(target_account_branch_id=2, new_status="HOLD")
        assert not can_foreign
        assert "scope violation" in msg2.lower()
        # Cannot set FLAGGED or CLOSED
        can_flag, msg3 = user.can_update_account(target_account_branch_id=1, new_status="FLAGGED")
        assert not can_flag
