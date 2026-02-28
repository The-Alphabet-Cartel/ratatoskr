"""
============================================================================
Bragi: Bot Infrastructure for The Alphabet Cartel
The Alphabet Cartel - https://discord.gg/alphabetcartel | alphabetcartel.net
============================================================================

MISSION - NEVER TO BE VIOLATED:
    Welcome  → Greet and orient new members to our chosen family
    Moderate → Support staff with tools that keep our space safe
    Support  → Connect members to resources, information, and each other
    Sustain  → Run reliably so our community always has what it needs

============================================================================
Example message handler for ratatoskr. Demonstrates the Bragi handler
pattern: plain classes with dependency injection, no Cog system (broken
in fluxer-py 0.3.1), called from a single dispatcher in main.py.

TODO: Rename this file and class to match your bot's purpose.
      This is a starting point — replace the example logic entirely.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-27
BOT: ratatoskr
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import time

import fluxer

from src.managers.config_manager import ConfigManager
from src.managers.logging_config_manager import LoggingConfigManager


class ExampleHandler:
    """Example handler demonstrating the Bragi handler pattern.

    Handlers are plain classes — no fluxer.Cog, no decorators.
    They receive dependencies via constructor injection and expose
    async methods called by the single dispatcher in main.py.

    fluxer-py only supports one registered handler per event type,
    so main.py acts as the central router.
    """

    def __init__(
        self,
        bot: fluxer.Bot,
        config_manager: ConfigManager,
        logging_manager: LoggingConfigManager,
    ) -> None:
        self.bot = bot
        self.config = config_manager
        self.log = logging_manager.get_logger("example_handler")
        self._recent_events: dict[str, float] = {}
        self._dedup_window = 5.0  # seconds — fluxer-py fires events twice

    # -------------------------------------------------------------------------
    # Dedup guard — fluxer-py delivers every event twice
    # -------------------------------------------------------------------------
    def _is_duplicate(self, key: str) -> bool:
        """Return True if this event key was seen within the dedup window."""
        now = time.monotonic()
        last = self._recent_events.get(key, 0.0)
        if now - last < self._dedup_window:
            return True
        self._recent_events[key] = now
        # Prune stale entries periodically
        if len(self._recent_events) > 500:
            cutoff = now - self._dedup_window
            self._recent_events = {
                k: v for k, v in self._recent_events.items() if v > cutoff
            }
        return False

    # -------------------------------------------------------------------------
    # Message handler
    # -------------------------------------------------------------------------
    async def handle_message(self, message: fluxer.Message) -> None:
        """Process an incoming message.

        Called from the single on_message dispatcher in main.py.
        fluxer-py Message quirks:
          - message.author is a User, NOT a GuildMember (no .roles)
          - message.guild does NOT exist — use message.channel.guild_id
          - message.content requires the message_content intent
        """
        # Dedup guard
        dedup_key = f"msg_{message.author.id}_{message.content[:50]}"
        if self._is_duplicate(dedup_key):
            return

        # TODO: Replace this example logic with your bot's actual behaviour
        self.log.debug(f"Message from {message.author.username}: {message.content[:80]}")


__all__ = ["ExampleHandler"]
