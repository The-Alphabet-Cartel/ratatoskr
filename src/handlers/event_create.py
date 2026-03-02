"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Event creation handler for Ratatoskr. Implements the DM-based wizard
for creating new operation events via the !event command.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import fluxer

from src.managers.config_manager import ConfigManager
from src.managers.database_manager import DatabaseManager
from src.managers.logging_config_manager import LoggingConfigManager
from src.utils.event_formatter import get_all_reaction_emoji, render_event_post
from src.utils.time_parser import TimeParseError, parse_event_time


class EventCreateHandler:
    """Handles the !event command — DM-based event creation wizard.

    Flow:
        1. User types !event in any channel
        2. Bot deletes the command message
        3. Bot DMs the user a three-step wizard:
           - Step 1: Operation name (title)
           - Step 2: Description / briefing
           - Step 3: Date and time (24-hour format)
        4. Bot posts the formatted event to RATATOSKR_EVENT_CHANNEL_ID
        5. Bot seeds the post with all role emoji reactions
        6. Bot DMs the user a confirmation with a link
    """

    def __init__(
        self,
        bot: fluxer.Bot,
        config_manager: ConfigManager,
        logging_manager: LoggingConfigManager,
        db: DatabaseManager,
        roles_config: dict[str, Any],
    ) -> None:
        self.bot = bot
        self.config = config_manager
        self.log = logging_manager.get_logger("event_create")
        self.db = db
        self.roles_config = roles_config
        self._dm_timeout = self.config.get_int("events", "dm_timeout_seconds", 300)
        self._tz_name = self.config.get("events", "timezone", "America/New_York")
        self._time_format = self.config.get(
            "events", "time_format_display", "%A, %B %d, %Y %H:%M"
        )
        self._event_channel_id = self.config.get("bot", "event_channel_id", "")
        self._command_staff_role_id = self.config.get(
            "bot", "command_staff_role_id", ""
        )

    async def handle(self, message: fluxer.Message) -> None:
        """Entry point — called from main.py dispatcher on !event."""
        author = message.author

        # Check Command Staff permission
        if not await self._is_command_staff(message):
            self.log.debug(f"Non-staff user {author.username} tried !event — ignoring")
            return

        # Start the DM wizard
        try:
            result = await self._run_wizard(author)
        except asyncio.TimeoutError:
            try:
                await author.send(
                    "⏰ Event creation timed out. Run `!event` to start over."
                )
            except Exception:
                pass
            return
        except Exception as e:
            self.log.error(f"Event creation wizard failed: {e}")
            try:
                await author.send("❌ Something went wrong. Please try again.")
            except Exception:
                pass
            return

        if result is None:
            return  # User cancelled

        title, description, event_time_utc = result

        # Post the event to the event channel
        try:
            event_msg = await self._post_event(
                title, description, event_time_utc, author
            )
        except Exception as e:
            self.log.error(f"Failed to post event: {e}")
            try:
                await author.send("❌ Failed to post the event. Please try again.")
            except Exception:
                pass
            return

        # Save to database
        event = await self.db.create_event(
            message_id=str(event_msg.id),
            channel_id=str(self._event_channel_id),
            creator_id=str(author.id),
            title=title,
            description=description,
            event_time=event_time_utc.isoformat(),
        )

        # Seed reactions
        await self._seed_reactions(event_msg)

        # Confirm to creator
        try:
            await author.send(
                f"✅ Event **{title}** created! "
                f"Check the event channel for the posting."
            )
        except Exception:
            pass

        self.log.info(f"Event created: '{title}' by {author.username} (id={event.id})")

    # =========================================================================
    # DM Wizard
    # =========================================================================

    async def _run_wizard(
        self, user: fluxer.User
    ) -> Optional[tuple[str, str, datetime]]:
        """Run the three-step DM wizard. Returns (title, description, utc_time) or None."""

        # Step 1: Title
        await user.send(
            "📋 **Create New Operation**\n\n"
            "**Step 1/3 — Operation Name**\n"
            "What is the name of this operation?\n\n"
            "_Type `cancel` to abort._"
        )
        title = await self._wait_for_dm(user)
        if title is None or title.lower() == "cancel":
            await user.send("❌ Event creation cancelled.")
            return None

        # Step 2: Description
        await user.send(
            "**Step 2/3 — Briefing / Description**\n"
            "Enter the operation briefing or description.\n\n"
            "_Type `cancel` to abort._"
        )
        description = await self._wait_for_dm(user)
        if description is None or description.lower() == "cancel":
            await user.send("❌ Event creation cancelled.")
            return None

        # Step 3: Time (with retry on parse failure)
        event_time_utc = await self._collect_time(user)
        if event_time_utc is None:
            return None

        return (title, description, event_time_utc)

    async def _collect_time(self, user: fluxer.User) -> Optional[datetime]:
        """Collect the event time with up to 3 retries on parse failure."""
        max_retries = 3
        for attempt in range(max_retries):
            prompt = (
                "**Step 3/3 — Date & Time (24-hour format)**\n"
                "When does the operation take place?\n\n"
                "Examples:\n"
                "• `Sunday, March 1, 2026 14:00`\n"
                "• `next Sunday 19:30`\n"
                "• `tomorrow 20:00`\n"
                "• `2026-03-01 14:00`\n\n"
                "_Type `cancel` to abort._"
            )
            if attempt > 0:
                prompt = "⚠️ Let's try again.\n\n" + prompt

            await user.send(prompt)
            raw = await self._wait_for_dm(user)
            if raw is None or raw.lower() == "cancel":
                await user.send("❌ Event creation cancelled.")
                return None

            try:
                return parse_event_time(raw, self._tz_name)
            except TimeParseError as e:
                await user.send(f"⚠️ {e}")

        await user.send("❌ Too many failed attempts. Run `!event` to start over.")
        return None

    async def _wait_for_dm(self, user: fluxer.User) -> Optional[str]:
        """Wait for a DM response from the user.

        TODO: This is the biggest Fluxer unknown. fluxer-py doesn't have
        bot.wait_for() like discord.py. Options:
          1. If fluxer-py supports wait_for: use it with a DM check
          2. If not: register a temporary on_message filter in the
             dispatcher that captures DMs from this user, using an
             asyncio.Event or asyncio.Queue to bridge the gap.
          3. Worst case: poll the DM channel for new messages.

        For now, this is stubbed with the wait_for pattern. We'll adapt
        after empirical testing on Fluxer.
        """

        def check(m):
            # Message is from the same user AND is a DM
            return m.author.id == user.id and getattr(m, "guild_id", None) is None

        try:
            # TODO: Confirm bot.wait_for exists in fluxer-py
            response = await self.bot.wait_for(
                "message", check=check, timeout=self._dm_timeout
            )
            return response.content.strip()
        except asyncio.TimeoutError:
            raise

    # =========================================================================
    # Posting and reactions
    # =========================================================================

    async def _post_event(
        self, title: str, description: str, event_time_utc: datetime, author
    ) -> fluxer.Message:
        """Post the formatted event to the event channel and return the message."""
        from src.models.event import Event

        # Build a temporary Event for rendering
        temp_event = Event(
            title=title,
            description=description,
            event_time=event_time_utc.isoformat(),
        )

        # Get creator display name from server
        creator_name = await self._get_display_name(author)

        # Render the post
        post_text = render_event_post(
            event=temp_event,
            signups=[],
            roles_config=self.roles_config,
            creator_display_name=creator_name,
            tz_name=self._tz_name,
            time_format=self._time_format,
        )

        # Send to event channel
        channel = await self.bot.fetch_channel(int(self._event_channel_id))
        event_msg = await channel.send(post_text)
        return event_msg

    async def _seed_reactions(self, message: fluxer.Message) -> None:
        """Add all role emoji + declined emoji as reactions to the event post."""
        emoji_list = get_all_reaction_emoji(self.roles_config)
        for emoji in emoji_list:
            try:
                # TODO: Confirm message.add_reaction(emoji) works for Unicode
                await message.add_reaction(emoji)
            except Exception as e:
                self.log.warning(f"Failed to add reaction {emoji}: {e}")
            # Small delay to avoid rate limits
            await asyncio.sleep(0.3)

    # =========================================================================
    # Permission and utility helpers
    # =========================================================================

    async def _is_command_staff(self, message: fluxer.Message) -> bool:
        """Check if the message author has the Command Staff role."""
        if not self._command_staff_role_id:
            self.log.warning("RATATOSKR_COMMAND_STAFF_ROLE_ID not set — denying all")
            return False

        try:
            # message.author is User, not GuildMember — must fetch
            # Learned from Prism: use guild.fetch_member()
            guild = await self.bot.fetch_guild(
                int(self.config.get("bot", "guild_id", "0"))
            )
            member = await guild.fetch_member(int(message.author.id))
            # member.roles is a flat list of integer role IDs (Prism finding)
            return int(self._command_staff_role_id) in member.roles
        except Exception as e:
            self.log.error(f"Permission check failed: {e}")
            return False

    async def _get_display_name(self, user) -> str:
        """Fetch the user's server nickname (includes rank prefix)."""
        try:
            guild = await self.bot.fetch_guild(
                int(self.config.get("bot", "guild_id", "0"))
            )
            member = await guild.fetch_member(int(user.id))
            return member.nick or member.username or str(user)
        except Exception as e:
            self.log.warning(f"Could not fetch display name for {user.id}: {e}")
            return str(user)


__all__ = ["EventCreateHandler"]
