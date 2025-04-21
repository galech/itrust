import asyncio
from datetime import datetime, timezone

from tzlocal import get_localzone


def convert_to_utc(dt: datetime, troncate_ms=False) -> datetime:
    dt = (dt if dt.tzinfo else dt.replace(tzinfo=get_localzone())).astimezone(timezone.utc)
    return dt.replace(microsecond=0) if troncate_ms else dt


def clear_redis_by_prefix(redis_client, prefix):
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor, match=f"{prefix}*", count=100)
        if keys:
            redis_client.delete(*keys)
        if cursor == 0:
            break


async def adapt_async(func, *args, **kwargs):
    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
