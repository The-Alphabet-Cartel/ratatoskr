"""
============================================================================
Bragi: Bot Infrastructure for The Alphabet Cartel
============================================================================
DM Collector for Ratatoskr. Provides a queue-based replacement for
discord.py's bot.wait_for() which does not exist in fluxer-py.

The on_message dispatcher feeds DM messages into the collector, and
handlers await responses via wait_for_dm().
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-03-03
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

log = logging.getLogger("ratatoskr.dm_collector")


class DMCollector:
    """Queue-based DM response collector.

    Usage:
        # In on_message dispatcher:
        if is_dm(message):
            dm_collector.feed(message)

        # In a handler:
        response = await dm_collector.wait_for_dm(user_id, timeout=300)
    """

    def __init__(self) -> None:
        # Maps user_id (str) → asyncio.Queue of message objects
        self._queues: dict[str, asyncio.Queue] = {}

    def feed(self, message) -> bool:
        """Feed a DM message into the collector.

        Called by the on_message dispatcher for every DM received.
        Returns True if a handler was waiting for this message,
        False if no one was listening (message is ignored).
        """
        user_id = str(message.author.id)
        queue = self._queues.get(user_id)
        if queue is not None:
            queue.put_nowait(message)
            log.debug(f"DM from {user_id} queued for waiting handler")
            return True
        return False

    async def wait_for_dm(
        self, user_id: str, timeout: float = 300.0
    ) -> Optional[str]:
        """Wait for a DM from a specific user.

        Args:
            user_id: The user snowflake to listen for.
            timeout: Seconds to wait before raising asyncio.TimeoutError.

        Returns:
            The message content as a stripped string.

        Raises:
            asyncio.TimeoutError: If no DM arrives within the timeout.
        """
        user_id = str(user_id)

        # Create a queue for this user (or reuse if somehow already exists)
        if user_id not in self._queues:
            self._queues[user_id] = asyncio.Queue()

        queue = self._queues[user_id]

        try:
            message = await asyncio.wait_for(queue.get(), timeout=timeout)
            return message.content.strip()
        except asyncio.TimeoutError:
            raise
        finally:
            # Clean up the queue when done (whether success or timeout)
            # Only remove if no other wait is pending
            if user_id in self._queues and self._queues[user_id].empty():
                del self._queues[user_id]

    def is_waiting(self, user_id: str) -> bool:
        """Check if a handler is currently waiting for DMs from this user."""
        return str(user_id) in self._queues

    def cancel(self, user_id: str) -> None:
        """Cancel any pending wait for a user (cleanup on error)."""
        user_id = str(user_id)
        if user_id in self._queues:
            del self._queues[user_id]
            log.debug(f"Cancelled DM wait for user {user_id}")


# Singleton instance — shared across all handlers
dm_collector = DMCollector()

__all__ = ["DMCollector", "dm_collector"]
