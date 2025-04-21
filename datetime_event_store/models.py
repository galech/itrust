from collections import namedtuple
from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel

DatetimeEventScore = namedtuple("DatetimeEventScore", ["timestamp", "id"])


class Event(BaseModel):
    id: Union[str, int]
    at: datetime
    data: str


class CursorPaginatedEvents(BaseModel):
    events: List[Event]
    next_cursor: Optional[str]
