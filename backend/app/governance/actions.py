"""
NexusDB Governed Write-Back Catalogue
Implements two-phase preview and confirmation flow for safe operational actions.
Never lets LLM emit UPDATE or DELETE statements; writes occur purely through parameterized routines.
"""

import hmac
import hashlib
import time
import json
from typing import Any
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db.session import get_db_connection
from app.governance.rbac import UserSession
from app.governance.audit import get_audit_manager

settings = get_settings()


class ActionPreview(BaseModel):
    action_name: str
    target_id: int
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    reason: str
    acting_role: str
    affected_rows: int
    confirmation_token: str
    expires_at: float


class ConfirmResult(BaseModel):
    success: bool
    message: str
    audit_seq: int
    action_name: str
    details: dict[str, Any] = Field(default_factory=dict)


# In-memory idempotency cache for confirmation requests (mapping idempotency_key to audit_seq)
_processed_idempotency_keys: dict[str, int] = {}


def generate_confirmation_token(user_id: str, action_name: str, params: dict[str, Any]) -> tuple[str, float]:
    expires_at = time.time() + settings.confirmation_token_expiry_seconds
    param_hash = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
    token_payload = f"{user_id}:{action_name}:{param_hash}:{expires_at}"
    sig = hmac.new(settings.jwt_secret.encode(), token_payload.encode(), hashlib.sha256).hexdigest()
    token = f"{token_payload}:{sig}"
    return token, expires_at


def verify_confirmation_token(token: str, user_id: str, action_name: str, params: dict[str, Any]) -> bool:
    parts = token.split(":")
    if len(parts) != 5:
        return False
    t_uid, t_action, t_hash, t_exp, t_sig = parts
    if t_uid != user_id or t_action != action_name:
        return False
    if float(t_exp) < time.time():
        return False
    param_hash = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
    if t_hash != param_hash:
        return False
    expected_payload = f"{t_uid}:{t_action}:{t_hash}:{t_exp}"
    expected_sig = hmac.new(settings.jwt_secret.encode(), expected_payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(t_sig, expected_sig)


class ActionManager:
    def __init__(self):
        self.audit = get_audit_manager()

    def preview_action(
        self,
        action_name: str,
        params: dict[str, Any],
        user: UserSession,
        request_id: str,
    ) -> ActionPreview:
        """Validates preconditions, RBAC, and generates a signed 2-minute confirmation token."""
        if action_name == "SET_ACCOUNT_STATUS":
            account_id = int(params.get("account_id", 0))
            new_status = str(params.get("new_status", "")).upper()
            reason = str(params.get("reason", "Operational status update"))

            # Precondition check 1: record exists
            with get_db_connection("nexus_reader") as conn:
                cur = conn.cursor()
                cur.execute("SELECT account_id, branch_id, status FROM accounts WHERE account_id = ?", (account_id,))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Account ID {account_id} not found in accounts table.")
                curr_acc_id, branch_id, curr_status = row[0], row[1], row[2]

            # Precondition check 2: current value differs
            if curr_status == new_status:
                raise ValueError(f"Account {account_id} is already in {new_status} status. No state change required.")

            # RBAC check with branch scope
            can_do, msg = user.can_update_account(target_account_branch_id=branch_id, new_status=new_status)
            if not can_do:
                self.audit.append_event(
                    request_id=request_id,
                    user_id=user.user_id,
                    role=user.role,
                    event_type="ACTION_DENIED",
                    status="DENIED",
                    payload={"action": action_name, "account_id": account_id, "reason": msg}
                )
                raise PermissionError(msg)

            # Generate confirmation token
            token, expires_at = generate_confirmation_token(user.user_id, action_name, params)

            # Audit action proposed
            self.audit.append_event(
                request_id=request_id,
                user_id=user.user_id,
                role=user.role,
                event_type="ACTION_PROPOSED",
                status="PROPOSED",
                payload={"action": action_name, "account_id": account_id, "from": curr_status, "to": new_status, "reason": reason}
            )

            return ActionPreview(
                action_name=action_name,
                target_id=account_id,
                before_state={"account_id": account_id, "status": curr_status, "branch_id": branch_id},
                after_state={"account_id": account_id, "status": new_status, "branch_id": branch_id},
                reason=reason,
                acting_role=user.role,
                affected_rows=1,
                confirmation_token=token,
                expires_at=expires_at,
            )

        elif action_name == "SET_RISK_FLAG":
            if not user.has_permission("action:set_risk_flag"):
                raise PermissionError("Your role does not have permission to place risk flags. It needs Credit Manager.")

            account_id = int(params.get("account_id", 0))
            flag_type = str(params.get("flag_type", "AML_SUSPICION"))
            severity = str(params.get("severity", "MEDIUM"))
            reason = str(params.get("reason", "Compliance review required"))

            with get_db_connection("nexus_reader") as conn:
                cur = conn.cursor()
                cur.execute("SELECT account_id FROM accounts WHERE account_id = ?", (account_id,))
                if not cur.fetchone():
                    raise ValueError(f"Account {account_id} does not exist.")

            token, expires_at = generate_confirmation_token(user.user_id, action_name, params)
            return ActionPreview(
                action_name=action_name,
                target_id=account_id,
                before_state={"account_id": account_id, "flag": None},
                after_state={"account_id": account_id, "flag_type": flag_type, "severity": severity},
                reason=reason,
                acting_role=user.role,
                affected_rows=1,
                confirmation_token=token,
                expires_at=expires_at,
            )

        raise NotImplementedError(f"Action {action_name} is not defined in the pre-authorized action catalog.")

    def execute_confirmed_action(
        self,
        action_name: str,
        params: dict[str, Any],
        confirmation_token: str,
        idempotency_key: str,
        user: UserSession,
        request_id: str,
    ) -> ConfirmResult:
        """Executes previewed action inside one transaction as nexus_writer with idempotency assert."""
        global _processed_idempotency_keys

        # Idempotency check: prevent duplicate execution on double-click
        if idempotency_key in _processed_idempotency_keys:
            return ConfirmResult(
                success=True,
                message="Action already applied previously (idempotency key matched).",
                audit_seq=_processed_idempotency_keys[idempotency_key],
                action_name=action_name,
            )

        # Validate token signature and expiry
        if not verify_confirmation_token(confirmation_token, user.user_id, action_name, params):
            raise PermissionError("Invalid or expired confirmation token. Write-back rejected.")

        if action_name == "SET_ACCOUNT_STATUS":
            account_id = int(params["account_id"])
            new_status = str(params["new_status"]).upper()
            reason = str(params.get("reason", ""))

            with get_db_connection("nexus_writer") as conn:
                cur = conn.cursor()
                # Apply change via parameterized SQL written by us
                cur.execute("UPDATE accounts SET status = ? WHERE account_id = ?", (new_status, account_id))
                rows_affected = cur.rowcount

                if rows_affected != 1:
                    raise RuntimeError(f"Safety assertion failed: expected 1 row affected, got {rows_affected}. Rolled back.")

            # Record in immutable audit log
            audit_ev = self.audit.append_event(
                request_id=request_id,
                user_id=user.user_id,
                role=user.role,
                event_type="ACTION_EXECUTED",
                status="SUCCESS",
                payload={"action": action_name, "account_id": account_id, "new_status": new_status, "reason": reason}
            )

            _processed_idempotency_keys[idempotency_key] = audit_ev.seq
            return ConfirmResult(
                success=True,
                message=f"Applied. Audit entry #{audit_ev.seq}",
                audit_seq=audit_ev.seq,
                action_name=action_name,
                details={"account_id": account_id, "new_status": new_status},
            )

        elif action_name == "SET_RISK_FLAG":
            account_id = int(params["account_id"])
            flag_type = str(params["flag_type"])
            severity = str(params["severity"])
            reason = str(params["reason"])

            with get_db_connection("nexus_writer") as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO risk_flags (account_id, flag_type, severity, reason, set_by) VALUES (?, ?, ?, ?, ?)",
                    (account_id, flag_type, severity, reason, user.username)
                )

            audit_ev = self.audit.append_event(
                request_id=request_id,
                user_id=user.user_id,
                role=user.role,
                event_type="ACTION_EXECUTED",
                status="SUCCESS",
                payload={"action": action_name, "account_id": account_id, "flag_type": flag_type, "severity": severity}
            )

            _processed_idempotency_keys[idempotency_key] = audit_ev.seq
            return ConfirmResult(
                success=True,
                message=f"Applied. Audit entry #{audit_ev.seq}",
                audit_seq=audit_ev.seq,
                action_name=action_name,
                details={"account_id": account_id, "flag_type": flag_type},
            )

        raise NotImplementedError(f"Action {action_name} not implemented.")


_action_manager: ActionManager | None = None


def get_action_manager() -> ActionManager:
    global _action_manager
    if _action_manager is None:
        _action_manager = ActionManager()
    return _action_manager
