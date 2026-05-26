import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_token
from app.core.database import get_db

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.users.service import get_or_create_user

    payload = await decode_token(credentials.credentials)

    keycloak_id = payload.get("sub")
    email = payload.get("email", "")
    username = payload.get("preferred_username", email)
    realm_roles = payload.get("realm_access", {}).get("roles", [])

    role = "VIEWER"
    if "ADMIN" in realm_roles:
        role = "ADMIN"
    elif "OPERATOR" in realm_roles:
        role = "OPERATOR"

    return await get_or_create_user(
        db=db,
        keycloak_id=uuid.UUID(keycloak_id),
        email=email,
        username=username,
        role=role,
    )
