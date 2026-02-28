"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Event data model for Ratatoskr. Represents a scheduled operation stored
in SQLite. Pure data class — no fluxer dependency.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Event:
    """Represents a scheduled operation/event."""

    # Database fields
    id: Optional[int] = None
    message_id: str = ""
    channel_id: str = ""
    creator_id: str = ""
    title: str = ""
    description: str = ""
    event_time: str = ""  # ISO 8601 UTC string
    created_at: str = ""
    reminder_sent: bool = False
    expired: bool = False

    # Convenience: parsed datetime (not stored, computed on access)
    _parsed_time: Optional[datetime] = field(default=None, repr=False)

    @property
    def event_datetime(self) -> Optional[datetime]:
        """Parse event_time string to datetime. Cached after first access."""
        if self._parsed_time is None and self.event_time:
            try:
                self._parsed_time = datetime.fromisoformat(self.event_time)
            except ValueError:
                return None
        return self._parsed_time

    @property
    def is_past(self) -> bool:
        """True if the event time has already passed."""
        dt = self.event_datetime
        if dt is None:
            return False
        return dt < datetime.now(timezone.utc)

    @classmethod
    def from_row(cls, row: dict) -> Event:
        """Construct an Event from a SQLite row dict."""
        return cls(
            id=row.get("id"),
            message_id=str(row.get("message_id", "")),
            channel_id=str(row.get("channel_id", "")),
            creator_id=str(row.get("creator_id", "")),
            title=row.get("title", ""),
            description=row.get("description", ""),
            event_time=row.get("event_time", ""),
            created_at=row.get("created_at", ""),
            reminder_sent=bool(row.get("reminder_sent", 0)),
            expired=bool(row.get("expired", 0)),
        )


__all__ = ["Event"]
