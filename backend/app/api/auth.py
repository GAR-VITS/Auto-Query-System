"""
NexusDB Authentication Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from passlib.hash import bcrypt

from app.db.session import get_db_connection
from app.governance.rbac import create_access_token, UserSession
from app.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    with get_db_connection("nexus_reader") as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, email, password_hash, role, branch_id FROM users WHERE username = ? OR email = ?", (req.username, req.username))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

        u_id, uname, email, pw_hash, role, branch_id = row[0], row[1], row[2], row[3], row[4], row[5]
        
        # Verify bcrypt password
        if not bcrypt.verify(req.password, pw_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

        token = create_access_token(user_id=str(u_id), username=uname, role=role, branch_id=branch_id)
        return LoginResponse(
            access_token=token,
            user={
                "user_id": u_id,
                "username": uname,
                "email": email,
                "role": role,
                "branch_id": branch_id,
            }
        )


@router.get("/me")
async def get_me(user: UserSession = Depends(get_current_user)):
    return {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "branch_id": user.branch_id,
    }
