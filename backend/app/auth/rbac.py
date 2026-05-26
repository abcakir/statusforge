from enum import Enum

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user


class Role(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


def require_role(*roles: Role):
    async def checker(user=Depends(get_current_user)):
        if user.role not in [r.value for r in roles]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return checker
