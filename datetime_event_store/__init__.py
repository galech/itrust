from .models import CursorPaginatedEvents, Event  # noqa: F401
from .store import DatetimeEventStore, MongoDBDatetimeEventStore, RedisDatetimeEventStore  # noqa: F401
from .utils import adapt_async  # noqa: F401


def genDatetimeEventStoreFromJson(json_data):
    return DatetimeEventStore(
        json_data["id"],
        [(item[0], item[1]) for item in json_data["ordered_events_meta"]],
        {int(k): v for k, v in json_data['events_by_id'].items()})
