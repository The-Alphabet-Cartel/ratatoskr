"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Reaction handler for Ratatoskr. Processes reaction add/remove events to
manage event signups with role enforcement.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================

NOTE: This handler has the highest risk of Fluxer API uncertainty.
The on_reaction_add / on_reaction_remove event signatures are UNCONFIRMED.
PerpetualPossum's rolebot confirms these events exist in fluxer-py, but
parameter shapes may differ from discord.py. All Fluxer API calls are
wrapped in try/except and marked with TODO comments for adaptation.
============================================================================
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Set

import fluxer

from src.managers.config_manager import ConfigManager
from src.managers.database_manager import DatabaseManager
from src.managers.logging_config_manager import LoggingConfigManager
from src.utils.event_formatter import (
    emoji_to_role_key,
    get_accepted_role_ids,
    render_event_post,
    role_key_to_emoji,
)


class ReactionHandler:
    """Processes reaction events for event signup management.

    Responsibilities:
        - Map emoji → role_key via roles_config
        - Enforce role membership (user must have the right server role)
        - Single signup per user (remove old reaction when switching)
        - Track signup in database
        - Re-render event message on changes
        - Prevent Command Staff from reacting
        - Distinguish bot-initiated reaction removals from user-initiated ones
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
        self.log = logging_manager.get_logger("reaction_handler")
        self.db = db
        self.roles_config = roles_config
        self._command_staff_role_id = self.config.get(
            "bot", "command_staff_role_id", ""
        )
        self._event_channel_id = self.config.get("bot", "event_channel_id", "")

        # Pending-removal set: tracks (message_id, user_id, emoji) tuples
        # that the BOT is about to remove. When on_reaction_remove fires
        # for these, we skip processing to avoid infinite loops.
        self._pending_removals: Set[tuple[str, str, str]] = set()

        # Debounce: tracks event_ids with pending re-renders
        self._render_pending: dict[int, asyncio.Task] = {}

    # =========================================================================
    # on_reaction_add
    # =========================================================================

    async def handle_add(self, reaction, user) -> None:
        """Process a reaction add event.

        TODO: The exact signature of (reaction, user) is UNCONFIRMED
        in fluxer-py. discord.py uses (reaction: Reaction, user: User).
        fluxer-py may pass different objects. Adapt after testing.

        Expected attributes (to be verified):
            reaction.message.id  — the message snowflake
            reaction.emoji       — the emoji (str or Emoji object)
            user.id              — the user snowflake
        """
        # Extract IDs — wrap in str() for safety
        message_id = str(reaction.message.id)
        user_id = str(user.id)
        emoji = str(reaction.emoji)

        # 1. Is this message a tracked event?
        event = await self.db.get_event_by_message_id(message_id)
        if event is None:
            return  # Not an event message — ignore

        # 2. Is this emoji in our config?
        role_key = emoji_to_role_key(emoji, self.roles_config)
        if role_key is None:
            # Unknown emoji — remove it
            await self._remove_reaction(reaction.message, emoji, user)
            return

        # 3. Block Command Staff from reacting
        if await self._is_command_staff(user):
            await self._remove_reaction(reaction.message, emoji, user)
            self.log.debug(f"Blocked Command Staff reaction from user {user_id}")
            return

        # 4. For role categories (not Declined): enforce role membership
        if role_key != "declined":
            if not await self._user_has_role(user, role_key):
                await self._remove_reaction(reaction.message, emoji, user)
                self.log.debug(f"User {user_id} lacks role for {role_key} — removed")
                return

        # 5. Check for existing signup — if switching, remove old reaction
        existing = await self.db.get_signup(event.id, user_id)
        if existing and existing.role_key != role_key:
            old_emoji = role_key_to_emoji(existing.role_key, self.roles_config)
            if old_emoji:
                await self._remove_reaction(reaction.message, old_emoji, user)

        # 6. Upsert the signup
        display_name = await self._get_display_name(user)
        await self.db.upsert_signup(
            event_id=event.id,
            user_id=user_id,
            display_name=display_name,
            role_key=role_key,
        )

        # 7. Re-render event message (debounced)
        await self._schedule_re_render(event.id)

    # =========================================================================
    # on_reaction_remove
    # =========================================================================

    async def handle_remove(self, reaction, user) -> None:
        """Process a reaction remove event."""
        message_id = str(reaction.message.id)
        user_id = str(user.id)
        emoji = str(reaction.emoji)

        # Check if this removal was bot-initiated (from handle_add switching)
        removal_key = (message_id, user_id, emoji)
        if removal_key in self._pending_removals:
            self._pending_removals.discard(removal_key)
            return  # Bot removed this — do NOT process as user action

        # Is this a tracked event?
        event = await self.db.get_event_by_message_id(message_id)
        if event is None:
            return

        # Is the emoji in our config?
        role_key = emoji_to_role_key(emoji, self.roles_config)
        if role_key is None:
            return

        # Does this user have a signup matching this role_key?
        existing = await self.db.get_signup(event.id, user_id)
        if existing and existing.role_key == role_key:
            await self.db.remove_signup(event.id, user_id)
            await self._schedule_re_render(event.id)

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _remove_reaction(self, message, emoji: str, user) -> None:
        """Remove a specific user's reaction, tracking it as bot-initiated."""
        removal_key = (str(message.id), str(user.id), emoji)
        self._pending_removals.add(removal_key)
        try:
            # TODO: Confirm the API for removing another user's reaction
            # discord.py uses message.remove_reaction(emoji, user)
            # fluxer-py may differ — may need HTTP DELETE
            await message.remove_reaction(emoji, user)
        except Exception as e:
            self.log.warning(
                f"Failed to remove reaction {emoji} from user {user.id}: {e}"
            )
            self._pending_removals.discard(removal_key)

    async def _is_command_staff(self, user) -> bool:
        """Check if user has the Command Staff role."""
        if not self._command_staff_role_id:
            return False
        try:
            guild = await self.bot.fetch_guild(
                int(self.config.get("bot", "guild_id", "0"))
            )
            member = await guild.fetch_member(int(user.id))
            return int(self._command_staff_role_id) in member.roles
        except Exception as e:
            self.log.error(f"Command Staff check failed: {e}")
            return False

    async def _user_has_role(self, user, role_key: str) -> bool:
        """Check if user has one of the accepted server roles for a signup category."""
        accepted_ids = get_accepted_role_ids(role_key, self.roles_config)
        if not accepted_ids:
            # No role_id configured for this category — allow anyone
            # (Will be restricted once role IDs are filled in)
            self.log.debug(f"No role_id set for {role_key} — allowing by default")
            return True
        try:
            guild = await self.bot.fetch_guild(
                int(self.config.get("bot", "guild_id", "0"))
            )
            member = await guild.fetch_member(int(user.id))
            user_role_ids = [str(r) for r in member.roles]
            return any(rid in user_role_ids for rid in accepted_ids)
        except Exception as e:
            self.log.error(f"Role check failed for user {user.id}: {e}")
            return False

    async def _get_display_name(self, user) -> str:
        """Fetch server nickname (with rank prefix)."""
        try:
            guild = await self.bot.fetch_guild(
                int(self.config.get("bot", "guild_id", "0"))
            )
            member = await guild.fetch_member(int(user.id))
            return member.nick or member.username or str(user)
        except Exception:
            return str(user)

    async def _schedule_re_render(self, event_id: int) -> None:
        """Debounced re-render: waits 100ms then re-renders.

        If multiple signups arrive in rapid succession, only the last
        one triggers a message edit, reducing API calls.
        """
        # Cancel any pending render for this event
        if event_id in self._render_pending:
            self._render_pending[event_id].cancel()

        self._render_pending[event_id] = asyncio.create_task(
            self._debounced_render(event_id)
        )

    async def _debounced_render(self, event_id: int) -> None:
        """Wait 100ms then re-render the event message."""
        await asyncio.sleep(0.1)

        try:
            event = await self.db.get_event_by_id(event_id)
            if event is None:
                return

            signups = await self.db.get_signups_for_event(event_id)

            # Fetch creator display name
            creator_name = ""
            try:
                guild = await self.bot.fetch_guild(
                    int(self.config.get("bot", "guild_id", "0"))
                )
                member = await guild.fetch_member(int(event.creator_id))
                creator_name = member.nick or member.username or ""
            except Exception:
                pass

            tz_name = self.config.get("events", "timezone", "America/New_York")
            time_format = self.config.get(
                "events", "time_format_display", "%A, %B %d, %Y %H:%M"
            )

            post_text = render_event_post(
                event=event,
                signups=signups,
                roles_config=self.roles_config,
                creator_display_name=creator_name,
                tz_name=tz_name,
                time_format=time_format,
            )

            # Edit the message in place
            channel = await self.bot.fetch_channel(int(self._event_channel_id))
            if channel:
                msg = await channel.fetch_message(int(event.message_id))
                if msg:
                    await msg.edit(content=post_text)

        except Exception as e:
            self.log.error(f"Re-render failed for event #{event_id}: {e}")
        finally:
            self._render_pending.pop(event_id, None)


__all__ = ["ReactionHandler"]
