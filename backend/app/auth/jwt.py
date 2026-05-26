import json
import logging
from typing import Any

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings
from app.core.redis import get_cache_redis

logger = logging.getLogger(__name__)

JWKS_CACHE_KEY = "jwks:keycloak"
JWKS_TTL = 3600


async def _fetch_jwks() -> dict[str, Any]:
    url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()


async def get_jwks() -> dict[str, Any]:
    cache = get_cache_redis()
    cached = await cache.get(JWKS_CACHE_KEY)
    if cached:
        return json.loads(cached)
    jwks = await _fetch_jwks()
    await cache.setex(JWKS_CACHE_KEY, JWKS_TTL, json.dumps(jwks))
    return jwks


async def decode_token(token: str) -> dict[str, Any]:
    try:
        jwks = await get_jwks()
        return jwt.decode(token, jwks, algorithms=["RS256"], audience=settings.keycloak_client_id)
    except JWTError as e:
        logger.warning("JWT validation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
