from datetime import UTC, datetime


def get_utc_now() -> datetime:
    """
    Returns timezone-aware datetime representing current time in UTC.
    """
    return datetime.now(UTC)


def format_iso_datetime(dt: datetime) -> str:
    """
    Converts datetime to ISO 8601 formatting.
    """
    if not dt:
        return ""
    # Ensure timezone info exists
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()
