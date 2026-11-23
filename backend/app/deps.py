"""
NexusDB Authentication Dependencies
Extracts and validates JWT Bearer tokens from incoming HTTP requests.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.governance.rbac import UserSession, decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> UserSession:
    if not credentials:
        # Default to viewer role for unauthenticated requests
        return UserSession(user_id="viewer", username="viewer@nexusdb.local", role="viewer")

    token = credentials.credentials
    user = decode_access_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
