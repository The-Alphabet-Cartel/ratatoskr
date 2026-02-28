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
Main entry point for Ratatoskr. Initialises managers, configures the Fluxer
client, loads handlers, registers event dispatchers, and starts the bot.

Single dispatcher pattern used because fluxer-py only supports one
registered handler per event type — registering a second silently
overwrites the first.
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-27
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import sys
import traceback

import fluxer

from src.managers.config_manager import create_config_manager
from src.managers.logging_config_manager import create_logging_config_manager


def main() -> None:

    # -------------------------------------------------------------------------
    # Initialise logging (must be first)
    # -------------------------------------------------------------------------
    logging_manager = create_logging_config_manager(app_name="ratatoskr")
    log = logging_manager.get_logger("main")

    log.info("ratatoskr starting up")

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
    # Validate token
    # -------------------------------------------------------------------------
    token = config_manager.get_token()
    if not token:
        log.critical("Bot token is missing — cannot start")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Initialise Fluxer client
    # -------------------------------------------------------------------------
    intents = fluxer.Intents.all() if hasattr(fluxer.Intents, 'all') else fluxer.Intents.default()
    intents.message_content = True
    intents.members = True
    # TODO: Enable additional intents as needed for your bot
    # intents.voice_states = True

    bot = fluxer.Bot(
        command_prefix=config_manager.get("bot", "command_prefix", "!"),
        intents=intents,
    )

    # -------------------------------------------------------------------------
    # Initialise managers
    # TODO: Add your bot-specific managers here using the factory pattern:
    #   my_manager = create_my_manager(
    #       config_manager=config_manager,
    #       logging_manager=logging_manager,
    #   )
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Initialise handlers
    # -------------------------------------------------------------------------
    from src.handlers.example_handler import ExampleHandler

    example = ExampleHandler(bot, config_manager, logging_manager)
    log.success("Loaded handler: example_handler")  # type: ignore[attr-defined]

    # TODO: Add additional handlers here. Each handler is a plain class —
    #       no Cog system (broken in fluxer-py 0.3.1).

    # -------------------------------------------------------------------------
    # Event dispatchers
    #
    # IMPORTANT: fluxer-py only supports ONE handler per event type.
    # Register a single dispatcher function that routes to all handlers.
    # -------------------------------------------------------------------------
    @bot.event
    async def on_message(message: fluxer.Message) -> None:
        """Single message dispatcher — routes to all message handlers."""
        if message.author.bot:
            return
        try:
            await example.handle_message(message)
        except Exception as e:
            log.error(
                f"example_handler error: {e}\n{traceback.format_exc()}"
            )
        # TODO: Add calls to additional handlers here

    # -------------------------------------------------------------------------
    # on_error — surface unhandled exceptions
    # -------------------------------------------------------------------------
    @bot.event
    async def on_error(event: str, *args, **kwargs) -> None:
        log.error(
            f"Unhandled exception in event '{event}':\n"
            f"{traceback.format_exc()}"
        )

    # -------------------------------------------------------------------------
    # on_ready — startup confirmation
    # -------------------------------------------------------------------------
    @bot.event
    async def on_ready() -> None:
        log.success(  # type: ignore[attr-defined]
            f"{ratatoskr} connected as {bot.user} (ID: {bot.user.id})"
        )
        # TODO: Add startup tasks here (reconciliation, background loops, etc.)

    # -------------------------------------------------------------------------
    # Start — bot.run() is blocking
    # -------------------------------------------------------------------------
    bot.run(token)


if __name__ == "__main__":
    main()
