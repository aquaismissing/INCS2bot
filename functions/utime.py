import datetime as dt


def utcnow() -> dt.datetime:
    """Timezone-aware version of deprecated ``datetime.datetime.utcnow()``."""

    return dt.datetime.now(dt.UTC)


def utcfromtimestamp(timestamp: float) -> dt.datetime:
    """Timezone-aware version of deprecated ``datetime.datetime.utcfromtimestamp()``."""

    return dt.datetime.fromtimestamp(timestamp, dt.UTC)
