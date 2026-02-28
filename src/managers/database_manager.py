"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
DatabaseManager for Ratatoskr. Async SQLite interface via aiosqlite.
Handles schema creation, event CRUD, and signup tracking.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiosqlite

from src.models.event import Event
from src.models.signup import Signup

log = logging.getLogger("ratatoskr.database_manager")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      TEXT NOT NULL UNIQUE,
    channel_id      TEXT NOT NULL,
    creator_id      TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    event_time      TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    reminder_sent   INTEGER NOT NULL DEFAULT 0,
    expired         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS signups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    role_key        TEXT NOT NULL,
    signed_up_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(event_id, user_id)
);
"""


class DatabaseManager:
    """Async SQLite database interface for events and signups."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Open database connection and create schema if needed."""
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._db.executescript(SCHEMA_SQL)
        await self._db.commit()
        log.info(f"Database initialized at {self._db_path}")

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
            log.info("Database connection closed")

    # =========================================================================
    # Event CRUD
    # =========================================================================

    async def create_event(
        self,
        message_id: str,
        channel_id: str,
        creator_id: str,
        title: str,
        description: str,
        event_time: str,
    ) -> Event:
        """Insert a new event and return the created Event."""
        assert self._db is not None
        cursor = await self._db.execute(
            """INSERT INTO events (message_id, channel_id, creator_id, title, description, event_time)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (message_id, channel_id, creator_id, title, description, event_time),
        )
        await self._db.commit()
        row_id = cursor.lastrowid
        log.debug(f"Created event id={row_id} title='{title}'")
        return Event(
            id=row_id,
            message_id=message_id,
            channel_id=channel_id,
            creator_id=creator_id,
            title=title,
            description=description,
            event_time=event_time,
        )

    async def get_event_by_message_id(self, message_id: str) -> Optional[Event]:
        """Look up an event by the Fluxer message snowflake."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT * FROM events WHERE message_id = ? AND expired = 0",
            (message_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return Event.from_row(dict(row))

    async def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Look up an event by database row ID."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT * FROM events WHERE id = ? AND expired = 0",
            (event_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return Event.from_row(dict(row))

    async def update_event(self, event_id: int, **fields: str) -> None:
        """Update one or more fields on an event."""
        assert self._db is not None
        allowed = {"title", "description", "event_time"}
        to_update = {k: v for k, v in fields.items() if k in allowed}
        if not to_update:
            return
        set_clause = ", ".join(f"{k} = ?" for k in to_update)
        values = list(to_update.values()) + [event_id]
        await self._db.execute(f"UPDATE events SET {set_clause} WHERE id = ?", values)
        await self._db.commit()
        log.debug(f"Updated event id={event_id}: {list(to_update.keys())}")

    async def mark_event_expired(self, event_id: int) -> None:
        """Mark an event as expired (soft delete)."""
        assert self._db is not None
        await self._db.execute(
            "UPDATE events SET expired = 1 WHERE id = ?", (event_id,)
        )
        await self._db.commit()
        log.debug(f"Marked event id={event_id} as expired")

    async def mark_reminder_sent(self, event_id: int) -> None:
        """Flag that the 15-minute reminder has been sent."""
        assert self._db is not None
        await self._db.execute(
            "UPDATE events SET reminder_sent = 1 WHERE id = ?", (event_id,)
        )
        await self._db.commit()

    async def get_events_needing_reminder(self) -> list[Event]:
        """Find active events starting within 15 minutes that haven't been reminded."""
        assert self._db is not None
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(minutes=15)
        cursor = await self._db.execute(
            """SELECT * FROM events
               WHERE expired = 0
                 AND reminder_sent = 0
                 AND event_time <= ?
                 AND event_time > ?""",
            (cutoff.isoformat(), now.isoformat()),
        )
        rows = await cursor.fetchall()
        return [Event.from_row(dict(r)) for r in rows]

    async def get_expired_events(self, cleanup_hours: int = 24) -> list[Event]:
        """Find active events that ended more than cleanup_hours ago."""
        assert self._db is not None
        cutoff = datetime.now(timezone.utc) - timedelta(hours=cleanup_hours)
        cursor = await self._db.execute(
            """SELECT * FROM events
               WHERE expired = 0
                 AND event_time < ?""",
            (cutoff.isoformat(),),
        )
        rows = await cursor.fetchall()
        return [Event.from_row(dict(r)) for r in rows]

    # =========================================================================
    # Signup CRUD
    # =========================================================================

    async def upsert_signup(
        self,
        event_id: int,
        user_id: str,
        display_name: str,
        role_key: str,
    ) -> Signup:
        """Insert or replace a user's signup for an event."""
        assert self._db is not None
        await self._db.execute(
            """INSERT INTO signups (event_id, user_id, display_name, role_key)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(event_id, user_id) DO UPDATE SET
                   display_name = excluded.display_name,
                   role_key = excluded.role_key,
                   signed_up_at = datetime('now')""",
            (event_id, user_id, display_name, role_key),
        )
        await self._db.commit()
        log.debug(f"Upserted signup: event={event_id} user={user_id} role={role_key}")
        return Signup(
            event_id=event_id,
            user_id=user_id,
            display_name=display_name,
            role_key=role_key,
        )

    async def remove_signup(self, event_id: int, user_id: str) -> bool:
        """Remove a user's signup. Returns True if a row was deleted."""
        assert self._db is not None
        cursor = await self._db.execute(
            "DELETE FROM signups WHERE event_id = ? AND user_id = ?",
            (event_id, user_id),
        )
        await self._db.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            log.debug(f"Removed signup: event={event_id} user={user_id}")
        return deleted

    async def get_signup(self, event_id: int, user_id: str) -> Optional[Signup]:
        """Get a specific user's signup for an event."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT * FROM signups WHERE event_id = ? AND user_id = ?",
            (event_id, user_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return Signup.from_row(dict(row))

    async def get_signups_for_event(self, event_id: int) -> list[Signup]:
        """Get all signups for an event, ordered by signup time."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT * FROM signups WHERE event_id = ? ORDER BY signed_up_at ASC",
            (event_id,),
        )
        rows = await cursor.fetchall()
        return [Signup.from_row(dict(r)) for r in rows]

    async def get_signups_for_reminder(self, event_id: int) -> list[Signup]:
        """Get all non-declined signups for reminder DMs."""
        assert self._db is not None
        cursor = await self._db.execute(
            """SELECT * FROM signups
               WHERE event_id = ? AND role_key != 'declined'
               ORDER BY signed_up_at ASC""",
            (event_id,),
        )
        rows = await cursor.fetchall()
        return [Signup.from_row(dict(r)) for r in rows]

    async def delete_signups_for_event(self, event_id: int) -> int:
        """Delete all signups for an event. Returns count deleted."""
        assert self._db is not None
        cursor = await self._db.execute(
            "DELETE FROM signups WHERE event_id = ?", (event_id,)
        )
        await self._db.commit()
        return cursor.rowcount


def create_database_manager(db_path: str) -> DatabaseManager:
    """Factory function — MANDATORY. Never call DatabaseManager directly."""
    return DatabaseManager(db_path=db_path)


__all__ = ["DatabaseManager", "create_database_manager"]
