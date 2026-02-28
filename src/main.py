"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Main entry point for Ratatoskr. Initialises managers, configures the Fluxer
client, loads handlers, registers event dispatchers, and starts the bot.

Single dispatcher pattern used because fluxer-py only supports one
registered handler per event type — registering a second silently
overwrites the first.
----------------------------------------------------------------------------
FILE VERSION: v2.0.0
LAST MODIFIED: 2026-02-28
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/the-alphabet-cartel/ratatoskr
============================================================================
"""

import sys

import fluxer

from src.managers.config_manager import create_config_manager
from src.managers.database_manager import create_database_manager
from src.managers.logging_config_manager import create_logging_config_manager
from src.handlers.channel_guard import ChannelGuardHandler
from src.handlers.event_create import EventCreateHandler
from src.handlers.event_manage import EventManageHandler
from src.handlers.reaction_handler import ReactionHandler
from src.handlers.reminder import ReminderHandler


# =============================================================================
# Deduplication guard — fluxer-py fires every gateway event TWICE
# Learned from Prism development. See fluxer-py quirks doc.
# =============================================================================
_seen_events: dict[str, float] = {}
_DEDUP_TTL = 2.0  # seconds


def _is_duplicate(event_key: str) -> bool:
    """Return True if this event was already processed within TTL."""
    import time

    now = time.time()
    # Prune old entries
    expired = [k for k, t in _seen_events.items() if now - t > _DEDUP_TTL]
    for k in expired:
        del _seen_events[k]
    if event_key in _seen_events:
        return True
    _seen_events[event_key] = now
    return False


def main() -> None:

    # -------------------------------------------------------------------------
    # Initialise logging (must be first)
    # -------------------------------------------------------------------------
    logging_manager = create_logging_config_manager(app_name="ratatoskr")
    log = logging_manager.get_logger("main")

    log.info("Ratatoskr starting up")

    # -------------------------------------------------------------------------
    # Initialise config
    # -------------------------------------------------------------------------
    try:
        config_manager = create_config_manager()
    except Exception as e:
        log.critical(f"Failed to initialise ConfigManager: {e}")
        sys.exit(1)

    # Re-initialise logging with config values
    logging_manager = create_logging_config_manager(
        log_level=config_manager.get("logging", "level", "INFO"),
        log_format=config_manager.get("logging", "format", "human"),
        log_file=config_manager.get("logging", "file"),
        console_enabled=config_manager.get_bool("logging", "console", True),
        app_name="ratatoskr",
    )
    log = logging_manager.get_logger("main")

    # -------------------------------------------------------------------------
    # Load roles config
    # -------------------------------------------------------------------------
    roles_config = config_manager.load_roles_config()
    role_count = len(roles_config.get("signup_roles", []))
    log.info(f"Loaded {role_count} signup roles from roles_config.json")

    # -------------------------------------------------------------------------
    # Validate token
    # -------------------------------------------------------------------------
    token = config_manager.get_token()
    if not token:
        log.critical("Bot token is missing — cannot start")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Initialise Fluxer client
    # -------------------------------------------------------------------------
    intents = (
        fluxer.Intents.all()
        if hasattr(fluxer.Intents, "all")
        else fluxer.Intents.default()
    )
    intents.message_content = True
    intents.members = True
    # TODO: Confirm guild_reactions intent exists in fluxer-py
    if hasattr(intents, "guild_reactions"):
        intents.guild_reactions = True

    bot = fluxer.Bot(intents=intents)

    # -------------------------------------------------------------------------
    # Create database manager (initialised async in on_ready)
    # -------------------------------------------------------------------------
    db_path = config_manager.get("database", "path", "/data/ratatoskr.db")
    db = create_database_manager(db_path)

    # -------------------------------------------------------------------------
    # Create handlers (wired with dependency injection)
    # -------------------------------------------------------------------------
    channel_guard = ChannelGuardHandler(bot, config_manager, logging_manager)
    event_create = EventCreateHandler(
        bot, config_manager, logging_manager, db, roles_config
    )
    event_manage = EventManageHandler(
        bot, config_manager, logging_manager, db, roles_config
    )
    reaction_handler = ReactionHandler(
        bot, config_manager, logging_manager, db, roles_config
    )
    reminder = ReminderHandler(bot, config_manager, logging_manager, db)

    # -------------------------------------------------------------------------
    # Command prefix
    # -------------------------------------------------------------------------
    prefix = config_manager.get("bot", "command_prefix", "!")

    # =========================================================================
    # Event dispatchers — ONE handler per event type (fluxer-py limitation)
    # =========================================================================

    @bot.event
    async def on_ready() -> None:
        log.success(f"Ratatoskr connected as {bot.user}")  # type: ignore[attr-defined]

        # Initialise database (async — can't do in main())
        await db.initialize()

        # Start background tasks
        await reminder.start()

        log.success("Ratatoskr is ready")

    @bot.event
    async def on_message(message: fluxer.Message) -> None:
        # Ignore bots
        if message.author.bot:
            return

        # Dedup guard — fluxer-py fires events twice
        dedup_key = f"msg-{message.id}"
        if _is_duplicate(dedup_key):
            return

        # Channel guard — delete non-bot messages from event channel
        # (still allow command processing after deletion)
        await channel_guard.handle(message)

        # Command routing
        if message.content.startswith(prefix):
            parts = message.content[len(prefix) :].strip().split()
            if not parts:
                return
            cmd = parts[0].lower()

            if cmd == "event":
                await event_create.handle(message)
            elif cmd == "edit":
                await event_manage.handle_edit(message)
            elif cmd == "delete":
                await event_manage.handle_delete(message)
            # Unknown commands are silently ignored

    @bot.event
    async def on_reaction_add(reaction, user) -> None:
        """Dispatcher for reaction add events.

        TODO: UNCONFIRMED SIGNATURE — the parameter types/names may
        differ in fluxer-py. Adapt after empirical testing.
        """
        if hasattr(user, "bot") and user.bot:
            return

        dedup_key = f"radd-{reaction.message.id}-{user.id}-{reaction.emoji}"
        if _is_duplicate(dedup_key):
            return

        await reaction_handler.handle_add(reaction, user)

    @bot.event
    async def on_reaction_remove(reaction, user) -> None:
        """Dispatcher for reaction remove events.

        TODO: UNCONFIRMED SIGNATURE — same caveat as on_reaction_add.
        """
        if hasattr(user, "bot") and user.bot:
            return

        dedup_key = f"rrem-{reaction.message.id}-{user.id}-{reaction.emoji}"
        if _is_duplicate(dedup_key):
            return

        await reaction_handler.handle_remove(reaction, user)

    # =========================================================================
    # Start the bot
    # =========================================================================
    log.info("Connecting to Fluxer gateway...")
    try:
        bot.run(token)
    except Exception as e:
        log.critical(f"Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
