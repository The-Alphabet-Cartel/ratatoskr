"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Signup data model for Ratatoskr. Represents a user's RSVP to an event.
Pure data class — no fluxer dependency.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Signup:
    """Represents a user's signup/attendance for an event."""

    id: Optional[int] = None
    event_id: int = 0
    user_id: str = ""
    display_name: str = ""  # Server nickname at time of signup (includes rank prefix)
    role_key: str = ""  # Key from roles_config (e.g., "operator", "declined")
    signed_up_at: str = ""

    @property
    def is_declined(self) -> bool:
        return self.role_key == "declined"

    @classmethod
    def from_row(cls, row: dict) -> Signup:
        """Construct a Signup from a SQLite row dict."""
        return cls(
            id=row.get("id"),
            event_id=row.get("event_id", 0),
            user_id=str(row.get("user_id", "")),
            display_name=row.get("display_name", ""),
            role_key=row.get("role_key", ""),
            signed_up_at=row.get("signed_up_at", ""),
        )


__all__ = ["Signup"]
