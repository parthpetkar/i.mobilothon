import redis.asyncio as redis
from app.config import REDIS_URL
import uuid
import asyncio

redis_client = redis.from_url(REDIS_URL)
LOCK_TTL = 30

async def acquire_lock(client, key: str, ttl: int = LOCK_TTL) -> bool:
    identifier = str(uuid.uuid4())
    if await client.set(key, identifier, nx=True, ex=ttl):
        return identifier  # Return for release
    return None

async def release_lock(client, key: str, identifier: str) -> bool:
    async with client.pipeline() as pipe:
        pipe.watch(key)
        if await client.get(key) == identifier:
            pipe.multi()
            pipe.delete(key)
            await pipe.execute()
            return True
    return False

async def acquire_lock_with_retry(redis_client, key, retries=3, delay=0.2):
    for _ in range(retries):
        lock_id = await acquire_lock(redis_client, key)
        if lock_id:
            return lock_id
        await asyncio.sleep(delay)
    return None