import base64
import json
from datetime import datetime, timezone
from itertools import count, islice
from typing import Optional

from bson import ObjectId
from dateutil.parser import isoparse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from sortedcontainers import SortedDict

from .models import DatetimeEventScore, Event
from .utils import clear_redis_by_prefix, convert_to_utc


class DatetimeEventStore:

    def __init__(self, initial_id=1):

        self._id_gen = count(start=initial_id)
        self.sorted_store = SortedDict()
        self.events_by_id = {}

    def clear(self):
        self.sorted_store.clear()
        self.events_by_id.clear()
        self._id_gen = count(start=1)  # reset IDs

    def gen_new_id(self):

        return next(self._id_gen)

    def compute_event_score(self, event_id):

        return self.events_by_id[event_id]["at"], event_id

    def get_event(self, event_id: int):
        return Event(**{**self.events_by_id[event_id], "id": event_id})

    def store_event(self, at: datetime, data: str):

        event_id = self.gen_new_id()
        self.sorted_store[DatetimeEventScore(convert_to_utc(at), event_id)] = event_id
        self.events_by_id[event_id] = {"at": convert_to_utc(at), "data": data}
        return self.get_event(event_id)

    def update_event(self, event_id: int, at: datetime = None, data: str = None):
        old_score = self.compute_event_score(event_id)
        self.events_by_id[event_id].update({
            **({} if data is None else {"data": data}),
            **({} if at is None else {"at": convert_to_utc(at)})
        })
        new_score = self.compute_event_score(event_id)
        if old_score != new_score:
            del self.sorted_store[old_score]
            self.sorted_store[new_score] = event_id
        return self.get_event(event_id)

    def delete_event(self, event_id):

        del self.sorted_store[self.compute_event_score(event_id)]
        del self.events_by_id[event_id]

    def get_events(self, start_date: datetime = None, end_date: datetime = None, cursor=None, limit=None, desc=False):

        start = DatetimeEventScore(start_date.isoformat(), 0) if start_date else None
        end = DatetimeEventScore(end_date.isoformat(), float('inf')) if end_date else None

        if cursor:
            if desc:
                end = self.raw_id_to_tuple(cursor)
            else:
                start = self.raw_id_to_tuple(cursor)

        raw_events = islice(
            self.sorted_store.irange(start, end, inclusive=((not cursor) or desc, not (cursor and desc)), reverse=desc),
            limit)
        if limit:
            return {
                "events": [self.get_event(store_event[1]) for store_event in raw_events],
                "next_cursor": raw_events[-1] if len(raw_events) == limit else None
            }

        return [self.get_event(store_event[1]) for store_event in raw_events]


class RedisDatetimeEventStore:

    def __init__(self, redis_client, sorted_key="sorted_events", hash_prefix="event:", prefix="qqqqqqqqqqevents"):

        self.redis = redis_client
        self.prefix = prefix
        self.sorted_key = f"{prefix}:{sorted_key}"
        self.hash_prefix = f"{prefix}:{hash_prefix}"
        self.id_key = f"{prefix}:next_id"

    def clear(self):
        clear_redis_by_prefix(self.redis, self.prefix)

    def gen_new_id(self):

        return self.redis.incr(self.id_key)

    def _hash_key(self, event_id: int):

        return f"{self.hash_prefix}{event_id}"

    def get_event(self, event_id: int):
        raw_event = self.redis.hgetall(self._hash_key(event_id))
        raw_event["at"] = isoparse(raw_event["at"])
        return Event(**{**raw_event, "id": event_id})

    def compute_event_score(self, event_id):

        return self._timestamp_to_score(datetime.fromisoformat(self.redis.hgetall(self._hash_key(event_id))["at"]),
                                        event_id)

    @staticmethod
    def _timestamp_to_score(dt: datetime, event_id: int):
        # we can only filter by seconds and we are limited to 999999 items
        return int(dt.timestamp()) + event_id * 1e-6

    def store_event(self, at: datetime, data: str):

        event_id = self.gen_new_id()
        pipe = self.redis.pipeline()
        pipe.zadd(self.sorted_key, {event_id: self._timestamp_to_score(convert_to_utc(at), event_id)})
        pipe.hset(self._hash_key(event_id), mapping={"at": convert_to_utc(at).isoformat(), "data": data})
        pipe.execute()
        return self.get_event(event_id)

    def delete_event(self, event_id: int):
        pipe = self.redis.pipeline()
        pipe.zrem(self.sorted_key, event_id)
        pipe.delete(self._hash_key(event_id))
        pipe.execute()

    def update_event(self, event_id: int, at: datetime = None, data: str = None):

        pipe = self.redis.pipeline()
        old_score = self.compute_event_score(event_id)
        pipe.hset(self._hash_key(event_id), mapping={
            **({} if data is None else {"data": data}),
            **({} if at is None else {"at": convert_to_utc(at).isoformat()})
        })
        new_score = self.compute_event_score(event_id)
        if old_score != new_score:
            pipe.zrem(self.sorted_key, event_id)
            pipe.zadd(self.sorted_key, {event_id: new_score})

        pipe.execute()
        return self.get_event(event_id)

    def get_events(self, start_date: datetime = None, end_date: datetime = None, cursor_score=None, limit=None,
                   desc=False):

        if desc:
            max_score = cursor_score or (int(end_date.timestamp()) if end_date else "+inf")
            min_score = int(start_date.timestamp()) if start_date else "-inf"
            ids = self.redis.zrevrangebyscore(self.sorted_key, max_score, min_score, 0 if limit else None,
                                              limit or None)
        else:
            min_score = cursor_score or (int(start_date.timestamp()) if start_date else "-inf")
            max_score = int(end_date.timestamp()) if end_date else "+inf"
            ids = self.redis.zrangebyscore(self.sorted_key, min_score, max_score, 0 if limit else None, limit or None)

        if limit:
            return {
                "events": [self.get_event(int(event_id)) for event_id in ids],
                "next_cursor": f"({self.redis.zscore(self.sorted_key, int(ids[-1]))}" if len(ids) == limit else None
            }

        return [self.get_event(int(event_id)) for event_id in ids]


class MongoDBDatetimeEventStore:

    # we lose microseconds precision

    def __init__(self, mongo_url: str, db_name: str, collection_name: str = "events"):

        self.client = AsyncIOMotorClient(mongo_url)
        self.collection = self.client[db_name][collection_name]

    async def clear(self):

        await self.collection.drop()

    async def setup(self):

        await self.collection.create_index([("at", DESCENDING), ("_id", DESCENDING)])
        await self.collection.create_index([("at", ASCENDING), ("_id", ASCENDING)])
        await self.collection.create_index([("at", ASCENDING)])
        await self.collection.create_index([("at", DESCENDING)])

    async def store_event(self, at: datetime, data: str):

        event = {"at": convert_to_utc(at, troncate_ms=True), "data": data}
        result = await self.collection.insert_one(event)
        return Event(**{**event, "id": str(result.inserted_id)})

    async def get_event(self, event_id: str):
        doc = await self.collection.find_one({"_id": ObjectId(event_id)})
        return self.doc_to_event(doc)

    async def update_event(self, event_id: str, at: Optional[datetime] = None, data: Optional[str] = None):
        await self.collection.update_one(
            {"_id": ObjectId(event_id)},
            {
                "$set": {
                    **({} if data is None else {"data": data}),
                    **({} if at is None else {"at": convert_to_utc(at, troncate_ms=True)})
                }
            })
        return await self.get_event(event_id)

    async def delete_event(self, event_id: str):
        await self.collection.delete_one({"_id": ObjectId(event_id)})

    @staticmethod
    def doc_to_event(doc):
        return Event(**{"id": str(doc["_id"]), "at": doc["at"].replace(tzinfo=timezone.utc), "data": doc["data"]})

    @staticmethod
    def encode_cursor(event) -> str:
        return base64.urlsafe_b64encode(
            json.dumps({"at": event["at"].isoformat(), "id": str(event["_id"])}).encode()).decode()

    @staticmethod
    def decode_cursor(cursor: str):
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return datetime.fromisoformat(payload["at"]), ObjectId(payload["id"])

    async def get_events(self,
                         start_date: datetime = None,
                         end_date: datetime = None,
                         cursor: str = None,
                         limit: int = None,
                         desc: bool = False,
                         ):

        conditions = []
        if start_date or end_date:
            at_conditions = {}
            if start_date:
                at_conditions["$gte"] = start_date
            if end_date:
                at_conditions["$lte"] = end_date
            conditions.append({"at": at_conditions})

        if cursor:
            ts, oid = self.decode_cursor(cursor)
            conditions.append({"$or": [
                {"at": {"$lt": ts} if desc else {"$gt": ts}},
                {
                    "at": ts,
                    "_id": {"$gt": oid}
                }
            ]})

        sort = DESCENDING if desc else ASCENDING
        query = self.collection.find(
            {"$and": conditions} if conditions else None
        ).sort([("at", sort), ("_id", sort)])
        if limit:
            events = await query.limit(limit).to_list(length=limit)
            return {
                "events": [self.doc_to_event(doc) for doc in events],
                "next_cursor": self.encode_cursor(events[-1]) if len(events) == limit else None
            }

        events = await query.to_list()
        return [self.doc_to_event(doc) for doc in events]
