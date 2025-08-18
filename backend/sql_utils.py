# sql_utils.py
# Driver-aware SQL utilities for PostgreSQL and SQLite compatibility

from datetime import datetime, timezone

def adapt_placeholders(db, query: str) -> str:
    """
    Convert %s → ? for sqlite; leave as-is for Postgres (psycopg2).
    """
    if getattr(db, "use_postgres", False):
        return query
    return query.replace("%s", "?")

def to_db_bool(db, value: bool):
    """
    Postgres supports boolean directly; sqlite stores as 0/1.
    """
    if getattr(db, "use_postgres", False):
        return bool(value)
    return 1 if bool(value) else 0

def to_db_ts(db, dt):
    """
    Postgres: pass datetime (timezone-aware preferred).
    sqlite: store ISO 8601 string.
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt  # assume already ISO string
    if getattr(db, "use_postgres", False):
        # Ensure tz-aware UTC for TIMESTAMPTZ
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    # sqlite
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def from_db_ts(db, raw):
    """
    Convert DB value back to datetime (best effort).
    """
    if raw is None:
        return None
    if getattr(db, "use_postgres", False):
        # psycopg2 returns datetime already
        return raw
    # sqlite -> parse ISO string
    try:
        # handle trailing Z
        s = raw.replace("Z", "+00:00") if isinstance(raw, str) else str(raw)
        return datetime.fromisoformat(s)
    except Exception:
        return None