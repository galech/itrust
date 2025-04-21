from datetime import datetime, timedelta, timezone

import pytest
import redis

from datetime_event_store import DatetimeEventStore, MongoDBDatetimeEventStore, RedisDatetimeEventStore
from datetime_event_store.utils import adapt_async, convert_to_utc


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
        assert event.data == "1", store
        assert event.at == utc_now, store
        now_local = datetime.now()
        event = await adapt_async(store.store_event, now_local, "1")
        assert event.at != now_local, store
        truncate_ms = getattr(store, "truncate_microseconds", False)
        assert convert_to_utc(event.at, truncate_ms) == convert_to_utc(now_local, truncate_ms), store


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
        await adapt_async(store.store_event, utc_past, "past")
        await adapt_async(store.store_event, utc_past_far, "past_far")
        await adapt_async(store.store_event, utc_future, "future")
        await adapt_async(store.store_event, utc_now, "now")
        await adapt_async(store.store_event, utc_future_far, "future_far")
        events = await adapt_async(store.get_events)
        assert len(events) == 5, store

        response = await adapt_async(store.get_events, utc_past, utc_future, None, 2, True)
        events = response["events"]
        assert len(events) == 2, store
        assert events[0].data == "future", store
        assert events[1].data == "now", store
        response = await adapt_async(store.get_events, utc_past, utc_future, response["next_cursor"], 1, True)
        events = response["events"]
        assert len(events) == 1, store
        assert events[0].data == "past", store
        empty_response = await adapt_async(store.get_events, utc_past, utc_future, response["next_cursor"], 2, True)
        assert len(empty_response["events"]) == 0, store
        response = await adapt_async(store.get_events, utc_past_far, utc_future, response["next_cursor"], 2, True)
        events = response["events"]
        assert len(events) == 1, store
        assert events[0].data == "past_far", store
        assert response["next_cursor"] is None, store

        response = await adapt_async(store.get_events, utc_past, utc_future, None, 2, False)
        events = response["events"]
        assert len(events) == 2, store
        assert events[0].data == "past", store
        assert events[1].data == "now", store
        response = await adapt_async(store.get_events, utc_past, utc_future, response["next_cursor"], 1, False)
        events = response["events"]
        assert len(events) == 1, store
        assert events[0].data == "future", store
        empty_response = await adapt_async(store.get_events, utc_past, utc_future, response["next_cursor"], 2, False)
        assert len(empty_response["events"]) == 0, store
        response = await adapt_async(store.get_events, utc_past, utc_future_far, response["next_cursor"], 2, False)
        events = response["events"]
        assert len(events) == 1, store
        assert events[0].data == "future_far", store
        assert response["next_cursor"] is None, store
# TODO test filters, pagination
