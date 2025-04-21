from .models import CursorPaginatedEvents, Event
from .store import DatetimeEventStore, Event, MongoDBDatetimeEventStore, RedisDatetimeEventStore
from .utils import adapt_async


def genDatetimeEventStoreFromJson(json_data):
    return DatetimeEventStore(
        json_data["id"],
        [(item[0], item[1]) for item in json_data["ordered_events_meta"]],
        {int(k): v for k, v in json_data['events_by_id'].items()})
