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
ConfigManager for Ratatoskr. Loads configuration from JSON defaults, then
overrides with .env values, then overrides sensitive values from Docker
Secrets. Implements the three-layer config stack (Rule #4 / Rule #7).
----------------------------------------------------------------------------
FILE VERSION: v1.0.0
LAST MODIFIED: 2026-02-27
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
Repository: https://github.com/PapaBearDoes/bragi
============================================================================
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("ratatoskr.config_manager")


class ConfigManager:
    """Three-layer configuration: JSON defaults → .env overrides → Docker Secrets."""

    def __init__(
        self, config_path: str = "/app/src/config/ratatoskr_config.json"
    ) -> None:
        self._config: dict[str, Any] = {}
        self._load_json(config_path)
        self._apply_env_overrides()
        self._apply_secret_overrides()

    # -------------------------------------------------------------------------
    # Layer 1: JSON defaults
    # -------------------------------------------------------------------------
    def _load_json(self, config_path: str) -> None:
        path = Path(config_path)
        if not path.exists():
            log.warning(
                f"⚠️ Config file not found at {config_path} — using empty defaults"
            )
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            log.debug(f"🔍 Loaded config from {config_path}")
        except (json.JSONDecodeError, OSError) as e:
            log.error(f"❌ Failed to load config JSON: {e} — using empty defaults")

    # -------------------------------------------------------------------------
    # Layer 2: .env overrides (non-sensitive)
    # -------------------------------------------------------------------------
    def _apply_env_overrides(self) -> None:
        """Map environment variables to config keys.

        TODO: Add your bot-specific env var mappings here.
              Convention: {BOT_PREFIX}_{CATEGORY}_{NAME} in SCREAMING_SNAKE_CASE
        """
        env_map = {
            # --- Logging (shared across all bots) ---
            "LOG_LEVEL": ("logging", "level"),
            "LOG_FORMAT": ("logging", "format"),
            "LOG_CONSOLE": ("logging", "console"),
            "RATATOSKR_LOG_FILE": ("logging", "file"),
            # --- Bot Behavior (shared across all bots) ---
            "COMMAND_PREFIX": ("bot", "command_prefix"),
            "GUILD_ID": ("bot", "guild_id"),
            # TODO: Add bot-specific env var mappings below
            # "{BOT_PREFIX}_SETTING_NAME": ("section", "key"),
        }
        for env_key, (section, key) in env_map.items():
            value = os.environ.get(env_key)
            if value is not None:
                self._config.setdefault(section, {})[key] = value
                log.debug(f"🔍 Applied env override: {env_key}")

    # -------------------------------------------------------------------------
    # Layer 3: Docker Secret overrides (sensitive)
    # -------------------------------------------------------------------------
    def _apply_secret_overrides(self) -> None:
        """Load sensitive values from Docker Secrets."""
        token_file = os.environ.get("TOKEN_FILE", "/run/secrets/ratatoskr_token")
        token = self._read_secret_file(token_file)
        if token:
            self._config.setdefault("bot", {})["token"] = token
            log.debug("🔍 Bot token loaded from Docker Secret")
        else:
            log.error("❌ Bot token not found — bot will fail to connect")

    def _read_secret_file(self, path: str) -> Optional[str]:
        secret_path = Path(path)
        if not secret_path.exists():
            log.warning(f"⚠️ Secret file not found: {path}")
            return None
        try:
            return secret_path.read_text(encoding="utf-8").strip()
        except OSError as e:
            log.error(f"❌ Could not read secret {path}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get a config value with an optional fallback."""
        return self._config.get(section, {}).get(key, fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get a config value as int, with safe fallback on bad data."""
        value = self.get(section, key, fallback)
        try:
            return int(value)
        except (TypeError, ValueError):
            log.warning(
                f"⚠️ [{section}.{key}] expected int, got {value!r} — using {fallback}"
            )
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = True) -> bool:
        """Get a config value as bool, with safe fallback on bad data."""
        value = self.get(section, key, fallback)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "yes")

    def get_token(self) -> str:
        """Convenience accessor for the bot token."""
        return self.get("bot", "token", "")


def create_config_manager(
    config_path: str = "/app/src/config/ratatoskr_config.json",
) -> ConfigManager:
    """Factory function — MANDATORY. Never call ConfigManager directly."""
    return ConfigManager(config_path=config_path)


__all__ = ["ConfigManager", "create_config_manager"]
