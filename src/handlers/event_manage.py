"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Event management handler for Ratatoskr. Handles !edit and !delete commands
for modifying or removing existing operations.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Optional

import fluxer

from src.managers.config_manager import ConfigManager
from src.managers.database_manager import DatabaseManager
from src.managers.logging_config_manager import LoggingConfigManager
from src.utils.event_formatter import render_event_post
from src.utils.time_parser import TimeParseError, parse_event_time


class EventManageHandler:
    """Handles !edit and !delete commands for event lifecycle management.

    Permission: Event creator OR Command Staff.
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
        self.log = logging_manager.get_logger("event_manage")
        self.db = db
        self.roles_config = roles_config
        self._tz_name = self.config.get("events", "timezone", "America/New_York")
        self._time_format = self.config.get(
            "events", "time_format_display", "%A, %B %d, %Y %H:%M"
        )
        self._dm_timeout = self.config.get_int("events", "dm_timeout_seconds", 300)
        self._command_staff_role_id = self.config.get(
            "bot", "command_staff_role_id", ""
        )
        self._event_channel_id = self.config.get("bot", "event_channel_id", "")

    # =========================================================================
    # !edit <id>
    # =========================================================================

    async def handle_edit(self, message: fluxer.Message) -> None:
        """Handle the !edit <id> command."""
        parts = message.content.strip().split(maxsplit=2)
        if len(parts) < 2:
            try:
                await message.author.send("Usage: `!edit <event_id>`")
            except Exception:
                pass
            return

        event_id = parts[1]
        try:
            event_id_int = int(event_id)
        except ValueError:
            try:
                await message.author.send(f"⚠️ '{event_id}' is not a valid event ID.")
            except Exception:
                pass
            return

        # Fetch event
        event = await self.db.get_event_by_id(event_id_int)
        if event is None:
            try:
                await message.author.send(f"⚠️ Event #{event_id} not found or expired.")
            except Exception:
                pass
            return

        # Permission check
        if not await self._can_manage(message.author, event):
            try:
                await message.author.send(
                    "⚠️ You don't have permission to edit this event."
                )
            except Exception:
                pass
            return

        # DM edit wizard — ask what to change
        author = message.author
        try:
            await author.send(
                f"✏️ **Editing Event #{event.id}: {event.title}**\n\n"
                "What would you like to change?\n"
                "• `title` — Change the operation name\n"
                "• `description` — Change the briefing\n"
                "• `time` — Change the date/time\n"
                "• `cancel` — Abort edit\n\n"
                "_Type your choice:_"
            )
            choice = await self._wait_for_dm(author)
            if choice is None or choice.lower() == "cancel":
                await author.send("❌ Edit cancelled.")
                return

            updates = {}
            choice = choice.lower().strip()

            if choice == "title":
                await author.send("Enter the new operation name:")
                new_title = await self._wait_for_dm(author)
                if new_title and new_title.lower() != "cancel":
                    updates["title"] = new_title

            elif choice == "description":
                await author.send("Enter the new briefing / description:")
                new_desc = await self._wait_for_dm(author)
                if new_desc and new_desc.lower() != "cancel":
                    updates["description"] = new_desc

            elif choice == "time":
                await author.send(
                    "Enter the new date and time (24-hour format):\n"
                    "Example: `Sunday, March 1, 2026 14:00`"
                )
                raw_time = await self._wait_for_dm(author)
                if raw_time and raw_time.lower() != "cancel":
                    try:
                        new_dt = parse_event_time(raw_time, self._tz_name)
                        updates["event_time"] = new_dt.isoformat()
                    except TimeParseError as e:
                        await author.send(f"⚠️ {e}")
                        return
            else:
                await author.send(f"⚠️ Unknown option: '{choice}'. Edit cancelled.")
                return

            if not updates:
                await author.send("❌ No changes made.")
                return

            # Apply updates
            await self.db.update_event(event.id, **updates)

            # Re-render and edit the event message
            await self._re_render_event(event.id)
            await author.send(f"✅ Event #{event.id} updated!")
            self.log.info(
                f"Event #{event.id} edited by {author.username}: {list(updates.keys())}"
            )

        except asyncio.TimeoutError:
            try:
                await author.send("⏰ Edit timed out.")
            except Exception:
                pass
        except Exception as e:
            self.log.error(f"Edit wizard failed: {e}")
            try:
                await author.send("❌ Something went wrong. Please try again.")
            except Exception:
                pass

    # =========================================================================
    # !delete <id>
    # =========================================================================

    async def handle_delete(self, message: fluxer.Message) -> None:
        """Handle the !delete <id> command."""
        parts = message.content.strip().split(maxsplit=2)
        if len(parts) < 2:
            try:
                await message.author.send("Usage: `!delete <event_id>`")
            except Exception:
                pass
            return

        event_id = parts[1]
        try:
            event_id_int = int(event_id)
        except ValueError:
            try:
                await message.author.send(f"⚠️ '{event_id}' is not a valid event ID.")
            except Exception:
                pass
            return

        event = await self.db.get_event_by_id(event_id_int)
        if event is None:
            try:
                await message.author.send(f"⚠️ Event #{event_id} not found or expired.")
            except Exception:
                pass
            return

        if not await self._can_manage(message.author, event):
            try:
                await message.author.send(
                    "⚠️ You don't have permission to delete this event."
                )
            except Exception:
                pass
            return

        # Confirm deletion via DM
        author = message.author
        try:
            await author.send(
                f"🗑️ **Delete Event #{event.id}: {event.title}?**\n\n"
                "Type `yes` to confirm deletion, or anything else to cancel."
            )
            response = await self._wait_for_dm(author)
            if response is None or response.lower() != "yes":
                await author.send("❌ Deletion cancelled.")
                return

            # Delete the message from the channel
            try:
                channel = await self.bot.fetch_channel(int(self._event_channel_id))
                if channel:
                    msg = await channel.fetch_message(int(event.message_id))
                    if msg:
                        await msg.delete()
            except Exception as e:
                self.log.warning(f"Could not delete event message: {e}")

            # Mark as expired and clean up signups
            await self.db.delete_signups_for_event(event.id)
            await self.db.mark_event_expired(event.id)
            await author.send(f"✅ Event #{event.id} deleted.")
            self.log.info(f"Event #{event.id} deleted by {author.username}")

        except asyncio.TimeoutError:
            try:
                await author.send("⏰ Delete confirmation timed out.")
            except Exception:
                pass
        except Exception as e:
            self.log.error(f"Delete failed: {e}")

    # =========================================================================
    # Shared helpers
    # =========================================================================

    async def _can_manage(self, user, event) -> bool:
        """Check if user is the event creator or Command Staff."""
        # Creator can always manage their own events
        if str(user.id) == str(event.creator_id):
            return True

        # Command Staff can manage any event
        if not self._command_staff_role_id:
            return False
        try:
            guild = await self.bot.fetch_guild(
                int(self.config.get("bot", "guild_id", "0"))
            )
            member = await guild.fetch_member(int(user.id))
            return int(self._command_staff_role_id) in member.roles
        except Exception as e:
            self.log.error(f"Permission check failed: {e}")
            return False

    async def _wait_for_dm(self, user) -> Optional[str]:
        """Wait for a DM response. Same pattern as event_create."""

        def check(m):
            return m.author.id == user.id and getattr(m, "guild_id", None) is None

        try:
            response = await self.bot.wait_for(
                "message", check=check, timeout=self._dm_timeout
            )
            return response.content.strip()
        except asyncio.TimeoutError:
            raise

    async def _re_render_event(self, event_id: int) -> None:
        """Re-fetch event + signups, render, and edit the message in place."""
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

        post_text = render_event_post(
            event=event,
            signups=signups,
            roles_config=self.roles_config,
            creator_display_name=creator_name,
            tz_name=self._tz_name,
            time_format=self._time_format,
        )

        try:
            channel = await self.bot.fetch_channel(int(self._event_channel_id))
            if channel:
                msg = await channel.fetch_message(int(event.message_id))
                if msg:
                    # TODO: Confirm message.edit(content=...) on Fluxer
                    await msg.edit(content=post_text)
        except Exception as e:
            self.log.error(f"Failed to re-render event #{event_id}: {e}")


__all__ = ["EventManageHandler"]
