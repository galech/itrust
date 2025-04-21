import os
from typing import List, Optional, Union

import redis
from dateutil.parser import isoparse
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from datetime_event_store import (
    CursorPaginatedEvents,
    DatetimeEventStore,
    Event,
    MongoDBDatetimeEventStore,
    RedisDatetimeEventStore,
    adapt_async,
)
from datetime_event_store.utils import gen_test_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EventInput(BaseModel):

    at: str  #
    data: str

    @property
    def at_datetime(self):

        return isoparse(self.at)
        
        
ENGINE = os.getenv("ENGINE", "mongo")
if ENGINE == "mongo":
    event_store = MongoDBDatetimeEventStore("mongodb://localhost:27017/", "test", "events")
elif ENGINE == "redis":
    event_store = RedisDatetimeEventStore(redis.Redis(host='localhost', port=6379, db=0, decode_responses=True))
else:
    event_store = DatetimeEventStore()


@app.on_event("startup")
async def startup():
    if os.getenv("CLEAR_STORE", "false") == "true":
        await adapt_async(event_store.clear)
    if hasattr(event_store, "setup"):
        await adapt_async(event_store.setup)
    if os.getenv("GEN_TEST_DATA", "false") == "true":
        await gen_test_data(event_store)

@app.post("/events/", response_model=Event)
async def create_event(event_input: EventInput):
    return await adapt_async(event_store.store_event, at=event_input.at_datetime, data=event_input.data)


@app.put("/events/{event_id}", response_model=Event)  # make patch available, params not required
async def update_event(event_id: str, event_input: EventInput):
    return await adapt_async(event_store.update_event, event_id, at=event_input.at_datetime, data=event_input.data)


@app.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    return await adapt_async(event_store.get_event, event_id)


@app.get("/events/", response_model=Union[List[Event], CursorPaginatedEvents])
async def get_events(
    start_date: Optional[str] = Query(None, alias="start"),
    end_date: Optional[str] = Query(None, alias="end"),
    cursor: Optional[str] = Query(None, description="page cursor"),
    page_size: Optional[int] = Query(None, alias="pageSize", description="page size"),
    order: Optional[str] = Query("asc", description="at order (asc, desc)")
):

    start_dt = isoparse(start_date) if start_date else None
    end_dt = isoparse(end_date) if end_date else None
    return await adapt_async(event_store.get_events, start_dt, end_dt, cursor, page_size, order == "desc")


@app.delete("/events/{event_id}")
async def delete_event(event_id: str):
    return await adapt_async(event_store.delete_event, event_id)


# TODO params sanitize
