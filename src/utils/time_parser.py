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
from datetime import datetime, timezone
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

    try:
        # dateutil.parser.parse handles most natural language formats
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
