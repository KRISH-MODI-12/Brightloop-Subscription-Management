from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Returns current datetime in UTC (timezone-aware).
    Replaces deprecated datetime.utcnow() cleanly and consistently.
    """
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """
    Returns current datetime in UTC as a naive datetime object.
    Useful for exact compatibility with legacy SQLite naive datetime columns.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

