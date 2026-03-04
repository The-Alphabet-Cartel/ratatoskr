"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Reaction handler for Ratatoskr. Processes raw reaction events to manage
event signups with role enforcement.
----------------------------------------------------------------------------
FILE VERSION: v2.0.0
LAST MODIFIED: 2026-03-03
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================

fluxer-py fires on_raw_reaction_add / on_raw_reaction_remove with a single
RawReactionActionEvent payload containing flat IDs:
    payload.channel_id  (int)
    payload.emoji       (str)
    payload.event_type  (str)  — "MESSAGE_REACTION_ADD" / "MESSAGE_REACTION_REMOVE"
    payload.guild_id    (int)
    payload.message_id  (int)
    payload.user_id     (int)

There are NO Reaction or User objects — everything is ID-based.
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
    """Processes raw reaction events for event signup management.

    Receives RawReactionActionEvent payloads with flat IDs.
    All Fluxer API lookups are done via fetch calls using those IDs.
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
        self._guild_id = self.config.get("bot", "guild_id", "0")

        # Pending-removal set: tracks (message_id, user_id, emoji) tuples
        # that the BOT is about to remove. When on_raw_reaction_remove fires
        # for these, we skip processing to avoid infinite loops.
        self._pending_removals: Set[tuple[str, str, str]] = set()

        # Debounce: tracks event_ids with pending re-renders
        self._render_pending: dict[int, asyncio.Task] = {}

    # =========================================================================
    # on_raw_reaction_add
    # =========================================================================

    async def handle_add(self, payload) -> None:
        """Process a raw reaction add event.

        Args:
            payload: RawReactionActionEvent with .message_id, .user_id,
                     .emoji, .channel_id, .guild_id
        """
        message_id = str(payload.message_id)
        user_id = str(payload.user_id)
        emoji = str(payload.emoji)

        self.log.debug(f"Reaction add: msg={message_id} user={user_id} emoji={emoji}")

        # 1. Is this message a tracked event?
        event = await self.db.get_event_by_message_id(message_id)
        if event is None:
            return  # Not an event message — ignore

        # 2. Is this emoji in our config?
        role_key = emoji_to_role_key(emoji, self.roles_config)
        if role_key is None:
            # Unknown emoji — remove it
            await self._remove_reaction(message_id, emoji, user_id)
            return

        # 3. For role categories (not Declined): enforce role membership
        #    Command Staff are NOT blocked — they sign up like anyone else,
        #    subject to the same role requirements.
        if role_key != "declined":
            if not await self._user_has_role(user_id, role_key):
                await self._remove_reaction(message_id, emoji, user_id)
                self.log.debug(f"User {user_id} lacks role for {role_key} — removed")
                return

        # 5. Check for existing signup — if switching, remove old reaction
        existing = await self.db.get_signup(event.id, user_id)
        if existing and existing.role_key != role_key:
            old_emoji = role_key_to_emoji(existing.role_key, self.roles_config)
            if old_emoji:
                await self._remove_reaction(message_id, old_emoji, user_id)

        # 6. Upsert the signup
        display_name = await self._get_display_name(user_id)
        await self.db.upsert_signup(
            event_id=event.id,
            user_id=user_id,
            display_name=display_name,
            role_key=role_key,
        )
        self.log.info(
            f"Signup: {display_name} → {role_key} for event #{event.id}"
        )

        # 7. Re-render event message (debounced)
        await self._schedule_re_render(event.id)

    # =========================================================================
    # on_raw_reaction_remove
    # =========================================================================

    async def handle_remove(self, payload) -> None:
        """Process a raw reaction remove event."""
        message_id = str(payload.message_id)
        user_id = str(payload.user_id)
        emoji = str(payload.emoji)

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
            self.log.info(f"Removed signup for user {user_id} from event #{event.id}")
            await self._schedule_re_render(event.id)

    # =========================================================================
    # Helpers — all use string IDs, no object dependencies
    # =========================================================================

    async def _remove_reaction(
        self, message_id: str, emoji: str, user_id: str
    ) -> None:
        """Remove a specific user's reaction via HTTP API.

        Tracks the removal as bot-initiated so on_raw_reaction_remove
        skips it instead of treating it as a user un-signup.
        """
        removal_key = (message_id, user_id, emoji)
        self._pending_removals.add(removal_key)
        try:
            # TODO: Confirm this API pattern works on Fluxer
            # fluxer-py may need direct HTTP DELETE instead
            channel = await self.bot.fetch_channel(int(self._event_channel_id))
            msg = await channel.fetch_message(int(message_id))
            if msg:
                await msg.remove_reaction(emoji, user_id)
        except Exception as e:
            self.log.warning(
                f"Failed to remove reaction {emoji} from user {user_id}: {e}"
            )
            self._pending_removals.discard(removal_key)

    async def _is_command_staff(self, user_id: str) -> bool:
        """Check if user has the Command Staff role."""
        if not self._command_staff_role_id:
            return False
        try:
            guild = await self.bot.fetch_guild(int(self._guild_id))
            member = await guild.fetch_member(int(user_id))
            return int(self._command_staff_role_id) in member.roles
        except Exception as e:
            self.log.error(f"Command Staff check failed: {e}")
            return False

    async def _user_has_role(self, user_id: str, role_key: str) -> bool:
        """Check if user has one of the accepted server roles for a signup category."""
        accepted_ids = get_accepted_role_ids(role_key, self.roles_config)
        if not accepted_ids:
            self.log.debug(f"No role_id set for {role_key} — allowing by default")
            return True
        try:
            guild = await self.bot.fetch_guild(int(self._guild_id))
            member = await guild.fetch_member(int(user_id))
            user_role_ids = [str(r) for r in member.roles]
            return any(rid in user_role_ids for rid in accepted_ids)
        except Exception as e:
            self.log.error(f"Role check failed for user {user_id}: {e}")
            return False

    async def _get_display_name(self, user_id: str) -> str:
        """Fetch server display name for a user."""
        try:
            guild = await self.bot.fetch_guild(int(self._guild_id))
            member = await guild.fetch_member(int(user_id))
            return member.display_name or member.user.username or user_id
        except Exception:
            return user_id

    async def _schedule_re_render(self, event_id: int) -> None:
        """Debounced re-render: waits 100ms then re-renders.

        If multiple signups arrive in rapid succession, only the last
        one triggers a message edit, reducing API calls.
        """
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
                guild = await self.bot.fetch_guild(int(self._guild_id))
                member = await guild.fetch_member(int(event.creator_id))
                creator_name = member.display_name or member.user.username or ""
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
                    self.log.debug(f"Re-rendered event #{event_id}")

        except Exception as e:
            self.log.error(f"Re-render failed for event #{event_id}: {e}")
        finally:
            self._render_pending.pop(event_id, None)


__all__ = ["ReactionHandler"]
