from __future__ import annotations
from redis.asyncio import Redis
from app.utils.redis_client import get_redis as _get_redis

def get_redis() -> Redis:
    return _get_redis()
