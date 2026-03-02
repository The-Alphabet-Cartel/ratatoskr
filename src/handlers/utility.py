"""
============================================================================
Bragi: Bot Infrastructure for The Alphabet Cartel
============================================================================
Utility handler for Ratatoskr. Provides admin-only staff commands for
server management. Currently implements !roles for listing guild roles
and their IDs — needed to configure roles_config.json.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-03-01
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

import fluxer

from src.managers.config_manager import ConfigManager
from src.managers.logging_config_manager import LoggingConfigManager


class UtilityHandler:
    """Admin-only utility commands. Currently: !roles."""

    def __init__(
        self,
        bot: fluxer.Bot,
        config_manager: ConfigManager,
        logging_manager: LoggingConfigManager,
    ) -> None:
        self.bot = bot
        self.config = config_manager
        self.log = logging_manager.get_logger("utility")
        self._guild_id = config_manager.get("bot", "guild_id", "")

    async def handle_roles(self, message: fluxer.Message) -> None:
        """List all guild roles and their IDs. Admin-only — silent ignore for non-admins."""

        # Fetch member and roles
        try:
            guild = await self.bot.fetch_guild(
                int(message.channel.guild_id)
            )
            member = await guild.fetch_member(message.author.id)
            roles = await guild.fetch_roles()
        except Exception as e:
            self.log.error(f"Could not fetch guild data: {e}")
            return

        # Check administrator permission (0x8 bitfield, same as Discord)
        member_role_ids = set(member.roles)
        is_admin = any(
            r for r in roles
            if r.id in member_role_ids and getattr(r, "permissions", 0) & 0x8
        )

        if not is_admin:
            self.log.debug(
                f"!roles ignored for {message.author.username} — not an administrator"
            )
            return

        self.log.info(f"!roles used by {message.author.username}")

        # Build output sorted by role position (highest first)
        lines = ["**Guild Roles and IDs:**\n```"]
        for role in sorted(roles, key=lambda r: r.position, reverse=True):
            lines.append(f"{role.name:<40} {role.id}")
        lines.append("```")

        output = "\n".join(lines)

        # Fluxer message limit assumed ~2000 chars (same as Discord)
        if len(output) <= 2000:
            await message.reply(output)
        else:
            # Chunk into multiple messages
            chunks = []
            chunk = ["**Guild Roles and IDs:**\n```"]
            for role in sorted(roles, key=lambda r: r.position, reverse=True):
                line = f"{role.name:<40} {role.id}"
                if sum(len(ln) for ln in chunk) + len(line) > 1900:
                    chunk.append("```")
                    chunks.append("\n".join(chunk))
                    chunk = ["```"]
                chunk.append(line)
            chunk.append("```")
            chunks.append("\n".join(chunk))
            for c in chunks:
                await message.reply(c)


__all__ = ["UtilityHandler"]
