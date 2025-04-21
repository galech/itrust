import asyncio
import random
from datetime import datetime, timedelta, timezone

from tzlocal import get_localzone


def convert_to_utc(dt: datetime, truncate_ms=False) -> datetime:
    dt = (dt if dt.tzinfo else dt.replace(tzinfo=get_localzone())).astimezone(timezone.utc)
    return dt.replace(microsecond=0) if truncate_ms else dt


def clear_redis_by_prefix(redis_client, prefix):
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor, match=f"{prefix}*", count=100)
        if keys:
            redis_client.delete(*keys)
        if cursor == 0:
            break


async def gen_test_data(store):

    start_ts = int((datetime.now() - timedelta(days=365)).timestamp())
    end_ts = int((datetime.now() + timedelta(days=30)).timestamp())
    for i in range(10000):
        dt = datetime.fromtimestamp(random.randint(start_ts, end_ts))
        await adapt_async(store.store_event, at=dt, data="Event number %d." % i)


async def adapt_async(func, *args, **kwargs):
    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
