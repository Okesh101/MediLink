# app/utils/time.py

from datetime import datetime
from zoneinfo import ZoneInfo

LAGOS_TZ = ZoneInfo("Africa/Lagos")


def lagos_now():
    return datetime.now(LAGOS_TZ)


def to_lagos_iso(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LAGOS_TZ)
    return dt.astimezone(LAGOS_TZ).isoformat()
