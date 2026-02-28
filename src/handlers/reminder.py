"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Reminder and cleanup background tasks for Ratatoskr.
- Sends DM reminders 15 minutes before events
- Removes expired event posts 24 hours after event time
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

import asyncio
import logging

import fluxer

from src.managers.config_manager import ConfigManager
from src.managers.database_manager import DatabaseManager
from src.managers.logging_config_manager import LoggingConfigManager


class ReminderHandler:
    """Background tasks for event reminders and expiry cleanup."""

    def __init__(
        self,
        bot: fluxer.Bot,
        config_manager: ConfigManager,
        logging_manager: LoggingConfigManager,
        db: DatabaseManager,
    ) -> None:
        self.bot = bot
        self.config = config_manager
        self.log = logging_manager.get_logger("reminder")
        self.db = db
        self._running = False

    async def start(self) -> None:
        """Start the background loops. Call once after bot is ready."""
        if self._running:
            return
        self._running = True
        self.log.info("Background tasks started")
        asyncio.create_task(self._reminder_loop())
        asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Signal background loops to stop."""
        self._running = False

    # =========================================================================
    # Reminder loop — checks every 60 seconds
    # =========================================================================

    async def _reminder_loop(self) -> None:
        """Send DM reminders for events starting within 15 minutes."""
        while self._running:
            try:
                events = await self.db.get_events_needing_reminder()
                for event in events:
                    await self._send_reminders_for_event(event)
                    await self.db.mark_reminder_sent(event.id)
            except Exception as e:
                self.log.error(f"Reminder loop error: {e}")

            await asyncio.sleep(60)

    async def _send_reminders_for_event(self, event) -> None:
        """DM all non-declined signups for an event."""
        signups = await self.db.get_signups_for_reminder(event.id)
        if not signups:
            return

        self.log.info(
            f"Sending reminders for '{event.title}' to {len(signups)} members"
        )
        for signup in signups:
            try:
                # TODO: Confirm DM sending pattern on Fluxer
                # Prism uses user.send() but DM channel creation may differ
                user = await self.bot.fetch_user(int(signup.user_id))
                if user:
                    await user.send(
                        f"⏰ **Reminder:** {event.title} starts in 15 minutes!"
                    )
            except Exception as e:
                self.log.warning(f"Failed to DM reminder to user {signup.user_id}: {e}")

    # =========================================================================
    # Cleanup loop — checks every 15 minutes
    # =========================================================================

    async def _cleanup_loop(self) -> None:
        """Delete event posts that ended more than cleanup_hours ago."""
        cleanup_hours = self.config.get_int("events", "cleanup_hours", 24)
        event_channel_id = self.config.get("bot", "event_channel_id", "")

        while self._running:
            try:
                expired_events = await self.db.get_expired_events(cleanup_hours)
                for event in expired_events:
                    await self._cleanup_event(event, event_channel_id)
                    await self.db.mark_event_expired(event.id)
            except Exception as e:
                self.log.error(f"Cleanup loop error: {e}")

            await asyncio.sleep(900)  # 15 minutes

    async def _cleanup_event(self, event, channel_id: str) -> None:
        """Delete the event message from the channel."""
        try:
            # TODO: Confirm channel.fetch_message() or HTTP fallback on Fluxer
            channel = await self.bot.fetch_channel(int(channel_id))
            if channel:
                message = await channel.fetch_message(int(event.message_id))
                if message:
                    await message.delete()
                    self.log.info(f"Cleaned up expired event: '{event.title}'")
        except Exception as e:
            self.log.warning(
                f"Failed to clean up event '{event.title}' "
                f"(msg_id={event.message_id}): {e}"
            )


__all__ = ["ReminderHandler"]
