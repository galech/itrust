from typing import List, Optional, Union

from dateutil.parser import isoparse
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from datetime_event_store import CursorPaginatedEvents, Event, MongoDBDatetimeEventStore

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


event_store = MongoDBDatetimeEventStore("mongodb://localhost:27017/", "test", "events")
# event_store = RedisDatetimeEventStore(redis.Redis(host='localhost', port=6379, db=0, decode_responses=True))
# event_store = DatetimeEventStore()


@app.on_event("startup")
async def startup():
    await event_store.setup()


@app.post("/events/", response_model=Event)
async def create_event(event_input: EventInput):
    return await event_store.store_event(at=event_input.at_datetime, data=event_input.data)


@app.put("/events/{event_id}", response_model=Event)  # make patch available, params not required
async def update_event(event_id: str, event_input: EventInput):
    updated_event = event_store.update_event(event_id, at=event_input.at_datetime, data=event_input.data)
    return await updated_event


@app.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    return await event_store.get_event(event_id)


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
    return await event_store.get_events(start_dt, end_dt, cursor, page_size, order == "desc")


@app.delete("/events/{event_id}")
async def delete_event(event_id: str):
    return await event_store.delete_event(event_id)


# TODO params sanitize
