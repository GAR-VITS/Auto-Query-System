"""
NexusDB Authentication & Role-Based Access Control (RBAC)
Enforces the permission matrix in Section 12 and validates row/branch scoping.
"""

from typing import Any
import jwt
from datetime import datetime, timezone, timedelta
from passlib.hash import bcrypt

from app.config import get_settings

settings = get_settings()

PERMISSIONS_MATRIX: dict[str, dict[str, str | bool]] = {
    "query:run": {"viewer": True, "branch_officer": True, "credit_manager": True, "admin": True},
    "schema:view": {"viewer": True, "branch_officer": True, "credit_manager": True, "admin": True},
    "action:set_account_status": {"viewer": False, "branch_officer": "limited", "credit_manager": True, "admin": False},
    "action:set_risk_flag": {"viewer": False, "branch_officer": False, "credit_manager": True, "admin": False},
    "action:clear_risk_flag": {"viewer": False, "branch_officer": False, "credit_manager": True, "admin": False},
    "audit:read_own": {"viewer": True, "branch_officer": True, "credit_manager": True, "admin": True},
    "audit:read_all": {"viewer": False, "branch_officer": False, "credit_manager": False, "admin": True},
    "audit:verify": {"viewer": False, "branch_officer": False, "credit_manager": False, "admin": True},
    "user:manage": {"viewer": False, "branch_officer": False, "credit_manager": False, "admin": True},
}


class UserSession:
    def __init__(self, user_id: str, username: str, role: str, branch_id: int | None = None):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.branch_id = branch_id

    def has_permission(self, permission: str) -> bool:
        perm_rule = PERMISSIONS_MATRIX.get(permission, {}).get(self.role, False)
        return bool(perm_rule)

    def can_update_account(self, target_account_branch_id: int | None, new_status: str) -> tuple[bool, str]:
        perm = PERMISSIONS_MATRIX["action:set_account_status"].get(self.role, False)
        if not perm:
            return False, f"Your role, {self.role.replace('_', ' ').title()}, cannot update account status. It needs Credit Manager or Branch Officer."

        if self.role == "branch_officer":
            # Branch officer can only set ACTIVE or HOLD, and only for accounts in their branch
            if new_status not in ("ACTIVE", "HOLD"):
                return False, f"Branch Officers may only set status to ACTIVE or HOLD (cannot set {new_status})."
            if self.branch_id is not None and target_account_branch_id != self.branch_id:
                return False, f"Branch Officer scope violation: account belongs to branch {target_account_branch_id}, not your assigned branch {self.branch_id}."

        return True, "OK"


def create_access_token(user_id: str, username: str, role: str, branch_id: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "branch_id": branch_id,
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> UserSession | None:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return UserSession(
            user_id=str(data.get("sub")),
            username=str(data.get("username", "")),
            role=str(data.get("role", "viewer")),
            branch_id=data.get("branch_id"),
        )
    except Exception:
        return None
