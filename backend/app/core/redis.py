import redis.asyncio as aioredis

from app.core.config import settings

_clients: dict[int, aioredis.Redis] = {}


def get_redis(db: int = 0) -> aioredis.Redis:
    if db not in _clients:
        _clients[db] = aioredis.from_url(
            settings.redis_url, db=db, decode_responses=True
        )
    return _clients[db]


def get_pubsub_redis() -> aioredis.Redis:
    return get_redis(db=1)


def get_cache_redis() -> aioredis.Redis:
    return get_redis(db=2)
