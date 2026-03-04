"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Natural language time parser for Ratatoskr. Accepts 24-hour military time
input and converts to timezone-aware datetime. No fluxer dependency.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
import pytz


class TimeParseError(Exception):
    """Raised when a time string cannot be parsed."""

    pass


def parse_event_time(
    raw_input: str,
    tz_name: str = "America/New_York",
) -> datetime:
    """Parse a natural language time string into a timezone-aware UTC datetime.

    Accepts formats like:
        - "Sunday, March 1, 2026 14:00"
        - "March 1 14:00"
        - "2026-03-01 14:00"
        - "next Sunday 19:30"
        - "tomorrow 20:00"

    Args:
        raw_input: The user's time string (24-hour format expected).
        tz_name: IANA timezone name for interpretation.

    Returns:
        A timezone-aware datetime in UTC.

    Raises:
        TimeParseError: If the input cannot be parsed or is in the past.
    """
    cleaned = raw_input.strip()
    if not cleaned:
        raise TimeParseError("No time provided. Please enter a date and time.")

    local_tz = _get_timezone(tz_name)
    now_local = datetime.now(local_tz)

    # Pre-process relative terms that dateutil doesn't understand
    parsed = _try_relative_parse(cleaned, now_local, local_tz)

    if parsed is None:
        # Fall back to dateutil for absolute dates
        try:
            parsed = dateutil_parser.parse(cleaned, fuzzy=True)
        except (ValueError, OverflowError) as e:
            raise TimeParseError(
                f"Could not understand '{cleaned}' as a date/time. "
                f"Try a format like 'Sunday, March 1, 2026 14:00'."
            ) from e

    # If no timezone info was provided, assume the configured local timezone
    if parsed.tzinfo is None:
        parsed = local_tz.localize(parsed)

    # Convert to UTC for storage
    utc_dt = parsed.astimezone(timezone.utc)

    # Reject past times
    now_utc = datetime.now(timezone.utc)
    if utc_dt < now_utc:
        raise TimeParseError(
            f"The time '{cleaned}' is in the past. "
            f"Please provide a future date and time."
        )

    return utc_dt


def format_event_time(
    utc_dt: datetime,
    tz_name: str = "America/New_York",
    fmt: str = "%A, %B %d, %Y %H:%M",
) -> str:
    """Format a UTC datetime for display in the configured timezone."""
    local_tz = _get_timezone(tz_name)
    local_dt = utc_dt.astimezone(local_tz)
    return local_dt.strftime(fmt)


def get_countdown(utc_dt: datetime) -> str:
    """Return a human-readable countdown string (e.g., 'in 2 days', 'in 3 hours')."""
    now = datetime.now(timezone.utc)
    if utc_dt <= now:
        return "started"

    delta = utc_dt - now
    total_seconds = int(delta.total_seconds())
    days = delta.days
    hours = total_seconds // 3600
    minutes = total_seconds // 60

    if days > 1:
        return f"in {days} days"
    elif days == 1:
        return "in 1 day"
    elif hours > 1:
        return f"in {hours} hours"
    elif hours == 1:
        return "in 1 hour"
    elif minutes > 1:
        return f"in {minutes} minutes"
    else:
        return "starting soon"


_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,
}

# Matches "tomorrow 17:45" or "next wednesday, 19:30" etc.
_RELATIVE_RE = re.compile(
    r"^(tomorrow|next\s+week|next\s+\w+)"
    r"[,\s]+(\d{1,2}:\d{2})"
    r"\s*$",
    re.IGNORECASE,
)


def _try_relative_parse(
    cleaned: str,
    now_local: datetime,
    local_tz: pytz.BaseTzInfo,
) -> Optional[datetime]:
    """Attempt to parse relative time expressions.

    Handles:
        - "tomorrow HH:MM"
        - "next week HH:MM" (same weekday, +7 days)
        - "next <weekday> HH:MM"

    Returns a tz-aware local datetime, or None if no relative pattern matched.
    """
    match = _RELATIVE_RE.match(cleaned.strip())
    if not match:
        return None

    relative_part = match.group(1).strip().lower()
    time_part = match.group(2).strip()

    # Parse the time portion
    try:
        hour, minute = map(int, time_part.split(":"))
    except ValueError:
        return None

    if relative_part == "tomorrow":
        target_date = now_local.date() + timedelta(days=1)
    elif relative_part == "next week":
        target_date = now_local.date() + timedelta(days=7)
    elif relative_part.startswith("next "):
        weekday_name = relative_part[5:].strip()
        target_weekday = _WEEKDAYS.get(weekday_name)
        if target_weekday is None:
            return None
        # Find the next occurrence of that weekday (always at least 1 day out)
        days_ahead = (target_weekday - now_local.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # "next Monday" when today is Monday = +7
        target_date = now_local.date() + timedelta(days=days_ahead)
    else:
        return None

    # Combine date + time in local timezone
    naive_dt = datetime.combine(target_date, datetime.min.time().replace(
        hour=hour, minute=minute
    ))
    return local_tz.localize(naive_dt)


def _get_timezone(tz_name: str) -> pytz.BaseTzInfo:
    """Resolve an IANA timezone name, falling back to UTC."""
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        return pytz.UTC


__all__ = [
    "TimeParseError",
    "parse_event_time",
    "format_event_time",
    "get_countdown",
]
