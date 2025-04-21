from datetime import datetime, timedelta, timezone

import pytest
import redis

from . import DatetimeEventStore, MongoDBDatetimeEventStore, RedisDatetimeEventStore
from .utils import adapt_async, convert_to_utc


@pytest.fixture
def datetime_event_store():
    return DatetimeEventStore()


@pytest.fixture
def redis_datetime_event_store():
    return RedisDatetimeEventStore(redis.Redis(host='localhost', port=6379, db=0, decode_responses=True), prefix="test")


@pytest.fixture
def mongodb_datetime_event_store():
    return MongoDBDatetimeEventStore("mongodb://localhost:27017/", "test", "events")


@pytest.fixture
def datetime_event_store():
    return DatetimeEventStore()


@pytest.fixture
def utc_now():
    return datetime.utcnow().replace(tzinfo=timezone.utc).replace(microsecond=0)  # Mongo db can fail on microseconds


@pytest.fixture
def utc_future(utc_now):
    return utc_now + timedelta(minutes=10)


@pytest.fixture
def utc_past(utc_now):
    return utc_now - timedelta(minutes=10)


@pytest.fixture
def utc_future_far(utc_now):
    return utc_now + timedelta(days=10)


@pytest.fixture
def utc_past_far(utc_now):
    return utc_now - timedelta(days=10)


@pytest.mark.asyncio
async def test_store_event(datetime_event_store, redis_datetime_event_store, mongodb_datetime_event_store, utc_now):
    for store in [datetime_event_store, redis_datetime_event_store, mongodb_datetime_event_store]:
        event = await adapt_async(store.store_event, utc_now, "1")
        assert event.detail == "1", store
        assert event.at == utc_now, store

        now_local = datetime.now()
        event = await adapt_async(store.store_event, now_local, "1")
        assert event.at != now_local, store
        assert event.at == convert_to_utc(now_local), store


@pytest.mark.asyncio
async def test_update_event(datetime_event_store, redis_datetime_event_store, mongodb_datetime_event_store, utc_now,
                            utc_past):
    for store in [datetime_event_store, redis_datetime_event_store, mongodb_datetime_event_store]:
        event = await adapt_async(store.store_event, utc_now, "1")
        updated_event = await adapt_async(store.update_event, event.id, utc_past, "1")
        assert updated_event.at == utc_past, store


@pytest.mark.asyncio
async def test_delete_event(datetime_event_store, redis_datetime_event_store, mongodb_datetime_event_store, utc_now):
    for store in [datetime_event_store, redis_datetime_event_store, mongodb_datetime_event_store]:
        event = await adapt_async(store.store_event, utc_now, "1")
        await adapt_async(store.delete_event, event.id), store


@pytest.mark.asyncio
async def test_get_events(datetime_event_store, redis_datetime_event_store, mongodb_datetime_event_store, utc_past_far,
                          utc_past, utc_now, utc_future, utc_future_far):
    for store in [datetime_event_store, redis_datetime_event_store, mongodb_datetime_event_store]:
        await adapt_async(store.clear)
        await adapt_async(store.store_event, utc_past, "2")
        await adapt_async(store.store_event, utc_past_far, "1")
        await adapt_async(store.store_event, utc_future, "4")
        await adapt_async(store.store_event, utc_now, "3")
        await adapt_async(store.store_event, utc_future_far, "5")
        events = await adapt_async(store.get_events)
        assert len(events) == 5, store

# TODO test filters, pagination
