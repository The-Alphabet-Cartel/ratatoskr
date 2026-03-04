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
from src.managers.config_watcher import create_config_watcher
from src.handlers.channel_guard import ChannelGuardHandler
from src.handlers.event_create import EventCreateHandler
from src.handlers.event_manage import EventManageHandler
from src.handlers.reaction_handler import ReactionHandler
from src.handlers.reminder import ReminderHandler
from src.handlers.utility import UtilityHandler
from src.utils.dm_collector import dm_collector


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
    utility = UtilityHandler(bot, config_manager, logging_manager)

    # -------------------------------------------------------------------------
    # Command prefix
    # -------------------------------------------------------------------------
    prefix = config_manager.get("bot", "command_prefix", "!")

    # -------------------------------------------------------------------------
    # Config watcher — hot-reload config files without container restart
    # -------------------------------------------------------------------------
    config_watcher = create_config_watcher(config_dir="/app/src/config")

    # Handlers that hold a roles_config reference and need updating on reload
    _roles_config_handlers = [event_create, event_manage, reaction_handler]

    async def _on_config_change(filename: str) -> None:
        """Callback fired by ConfigWatcher when a JSON file is modified."""
        if filename == "roles_config.json":
            new_roles = config_manager.load_roles_config()
            for handler in _roles_config_handlers:
                handler.roles_config = new_roles
            role_count = len(new_roles.get("signup_roles", []))
            log.info(f"Hot-reloaded roles_config.json — {role_count} signup roles")

        elif filename == "ratatoskr_config.json":
            # Main config reload is trickier — env/secrets still override.
            # For now, log and advise restart for non-roles config changes.
            log.warning(
                f"{filename} changed — restart the container to apply "
                f"main config changes (roles_config hot-reloads automatically)"
            )

    config_watcher.on_change(_on_config_change)

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
        await config_watcher.start()

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

        # DM routing — feed DMs to the collector for wizard handlers.
        # If a handler is waiting for this user's DM, consume it and stop.
        # guild_id is None for DMs in fluxer-py.
        if getattr(message, "guild_id", None) is None:
            if dm_collector.feed(message):
                return  # A handler consumed this DM
            # No handler waiting — ignore unsolicited DMs
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
            elif cmd == "roles":
                await utility.handle_roles(message)
            elif cmd == "probe":
                # DIAGNOSTIC: Inspect GuildMember attributes
                # Usage: !probe
                # REMOVE after discovery
                try:
                    guild = await bot.fetch_guild(
                        int(config_manager.get("bot", "guild_id", "0"))
                    )
                    member = await guild.fetch_member(message.author.id)
                    attrs = [a for a in dir(member) if not a.startswith("_")]
                    log.warning(f"🔬 GuildMember attrs: {attrs}")
                    # Try common name attributes
                    for attr in ["username", "name", "display_name", "nick", "global_name", "user"]:
                        val = getattr(member, attr, "N/A")
                        log.warning(f"🔬   member.{attr} = {val!r}")
                        if attr == "user" and val != "N/A":
                            user_attrs = [a for a in dir(val) if not a.startswith("_")]
                            log.warning(f"🔬   member.user attrs: {user_attrs}")
                            for ua in ["username", "name", "display_name", "global_name", "id"]:
                                log.warning(f"🔬     member.user.{ua} = {getattr(val, ua, 'N/A')!r}")
                    await message.reply(f"Probe logged — check container logs")
                except Exception as e:
                    log.error(f"Probe failed: {e}")
                    await message.reply(f"Probe error: {e}")
            # Unknown commands are silently ignored

    # =========================================================================
    # DIAGNOSTIC: Reaction event discovery
    # fluxer-py does NOT fire on_reaction_add — we need to find the real name.
    # Register multiple candidates; whichever fires tells us the answer.
    # Also probe GuildMember attributes for the .username fix.
    # REMOVE THIS BLOCK after discovery and replace with real handlers.
    # =========================================================================

    @bot.event
    async def on_reaction_add(*args, **kwargs) -> None:
        log.warning(f"🔬 PROBE: on_reaction_add fired! args={len(args)} types={[type(a).__name__ for a in args]} kwargs={list(kwargs.keys())}")
        for i, arg in enumerate(args):
            log.warning(f"🔬   arg[{i}] ({type(arg).__name__}): {dir(arg)}")

    @bot.event
    async def on_message_reaction_add(*args, **kwargs) -> None:
        log.warning(f"🔬 PROBE: on_message_reaction_add fired! args={len(args)} types={[type(a).__name__ for a in args]} kwargs={list(kwargs.keys())}")
        for i, arg in enumerate(args):
            log.warning(f"🔬   arg[{i}] ({type(arg).__name__}): {dir(arg)}")

    @bot.event
    async def on_raw_reaction_add(*args, **kwargs) -> None:
        log.warning(f"🔬 PROBE: on_raw_reaction_add fired! args={len(args)} types={[type(a).__name__ for a in args]} kwargs={list(kwargs.keys())}")
        for i, arg in enumerate(args):
            log.warning(f"🔬   arg[{i}] ({type(arg).__name__}): {dir(arg)}")

    # Also probe GuildMember attributes when !roles runs
    @bot.event
    async def on_guild_member_add(*args, **kwargs) -> None:
        log.warning(f"🔬 PROBE: on_guild_member_add fired! args={len(args)}")

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
