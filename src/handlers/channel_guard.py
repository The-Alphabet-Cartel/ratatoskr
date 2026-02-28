"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Channel guard handler for Ratatoskr. Deletes non-bot messages from the
event channel to keep it clean. Mirrors Apollo's channel behavior.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

import logging

import fluxer

from src.managers.config_manager import ConfigManager
from src.managers.logging_config_manager import LoggingConfigManager


class ChannelGuardHandler:
    """Deletes non-bot messages from the configured event channel.

    Any message in EVENT_CHANNEL_ID that was not sent by the bot
    is deleted immediately. This keeps the event channel as a clean
    feed of operation postings only — no chatter, no stray commands.
    """

    def __init__(
        self,
        bot: fluxer.Bot,
        config_manager: ConfigManager,
        logging_manager: LoggingConfigManager,
    ) -> None:
        self.bot = bot
        self.config = config_manager
        self.log = logging_manager.get_logger("channel_guard")
        self._event_channel_id = self.config.get("bot", "event_channel_id", "")

    async def should_delete(self, message: fluxer.Message) -> bool:
        """Check if this message should be deleted from the event channel.

        Returns True if the message is in the event channel and was NOT
        sent by the bot itself.
        """
        if not self._event_channel_id:
            return False

        # Compare as strings — fluxer IDs may be int or str
        if str(message.channel.id) != str(self._event_channel_id):
            return False

        # Don't delete the bot's own messages
        if message.author.id == self.bot.user.id:
            return False

        return True

    async def handle(self, message: fluxer.Message) -> bool:
        """Delete the message if it's in the event channel.

        Returns True if the message was deleted, False otherwise.
        The caller (main.py dispatcher) should still process commands
        from the message content even after deletion.
        """
        if not await self.should_delete(message):
            return False

        try:
            await message.delete()
            self.log.debug(
                f"Deleted message from {message.author.username} in event channel"
            )
        except Exception as e:
            # TODO: Test message.delete() on Fluxer — may need HTTP fallback
            self.log.warning(f"Failed to delete message: {e}")

        return True


__all__ = ["ChannelGuardHandler"]
