"""
============================================================================
Ratatoskr: Bot Infrastructure
============================================================================
Event post formatter for Ratatoskr. Renders the event message text from
an Event, its signups, and the roles config. No fluxer dependency.
----------------------------------------------------------------------------
FILE VERSION: v1.1.0
LAST MODIFIED: 2026-03-03
BOT: Ratatoskr
CLEAN ARCHITECTURE: Compliant
============================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.models.event import Event
from src.models.signup import Signup
from src.utils.time_parser import format_event_time, get_countdown


def render_event_post(
    event: Event,
    signups: list[Signup],
    roles_config: dict[str, Any],
    creator_display_name: str = "",
    tz_name: str = "America/New_York",
    time_format: str = "%A, %B %d, %Y %H:%M",
) -> str:
    """Render the full event post message text.

    Args:
        event: The Event data model.
        signups: All signups for this event.
        roles_config: The parsed roles_config.json dict.
        creator_display_name: Server nickname of the event creator.
        tz_name: Timezone for display.
        time_format: strftime format for the event time.

    Returns:
        The complete formatted message string.
    """
    lines: list[str] = []

    # Header
    lines.append("═══════════════════════════════════════")
    lines.append(f"📋 {event.title}")
    lines.append("")

    # Description
    if event.description:
        lines.append(event.description)
        lines.append("")

    # Time section
    event_dt = event.event_datetime
    if event_dt:
        display_time = format_event_time(event_dt, tz_name, time_format)
        countdown = get_countdown(event_dt)
        lines.append(f"⏰ Time")
        lines.append(display_time)
        lines.append(f"⏳ {countdown}")
    lines.append("")

    # Divider
    lines.append("───────────────────────────────────────")

    # Build a lookup: role_key -> list of signups
    signups_by_role: dict[str, list[Signup]] = {}
    for signup in signups:
        signups_by_role.setdefault(signup.role_key, []).append(signup)

    # Render each signup role section (in config order)
    signup_roles = roles_config.get("signup_roles", [])
    for role_def in signup_roles:
        key = role_def["key"]
        label = role_def["label"]
        emoji = role_def["emoji"]
        role_signups = signups_by_role.get(key, [])
        count = len(role_signups)

        if count > 0:
            lines.append(f"{emoji} {label} ({count})")
            for s in role_signups:
                lines.append(f"  {s.display_name}")
        else:
            lines.append(f"{emoji} {label}")
            lines.append("  —")
        lines.append("")

    # Declined section
    declined_config = roles_config.get("declined", {})
    declined_emoji = declined_config.get("emoji", "❌")
    declined_label = declined_config.get("label", "Declined")
    declined_signups = signups_by_role.get("declined", [])
    declined_count = len(declined_signups)

    if declined_count > 0:
        lines.append(f"{declined_emoji} {declined_label} ({declined_count})")
        for s in declined_signups:
            lines.append(f"  {s.display_name}")
    else:
        lines.append(f"{declined_emoji} {declined_label}")
        lines.append("  —")
    lines.append("")

    # Footer
    lines.append(f"📌 Event ID: {event.id}")
    if creator_display_name:
        lines.append(f"Created by {creator_display_name}")
    lines.append("═══════════════════════════════════════")

    return "\n".join(lines)


def get_all_reaction_emoji(roles_config: dict[str, Any]) -> list[str]:
    """Return the ordered list of emoji to seed on a new event post."""
    emoji_list = []
    for role_def in roles_config.get("signup_roles", []):
        emoji_list.append(role_def["emoji"])
    # Declined emoji always last
    declined_config = roles_config.get("declined", {})
    declined_emoji = declined_config.get("emoji", "❌")
    emoji_list.append(declined_emoji)
    return emoji_list


def emoji_to_role_key(emoji: str, roles_config: dict[str, Any]) -> str | None:
    """Map an emoji string to its role_key, or None if not found."""
    for role_def in roles_config.get("signup_roles", []):
        if role_def["emoji"] == emoji:
            return role_def["key"]
    declined_config = roles_config.get("declined", {})
    if declined_config.get("emoji") == emoji:
        return "declined"
    return None


def role_key_to_emoji(role_key: str, roles_config: dict[str, Any]) -> str | None:
    """Map a role_key to its emoji string, or None if not found."""
    if role_key == "declined":
        return roles_config.get("declined", {}).get("emoji", "❌")
    for role_def in roles_config.get("signup_roles", []):
        if role_def["key"] == role_key:
            return role_def["emoji"]
    return None


def get_accepted_role_ids(role_key: str, roles_config: dict[str, Any]) -> list[str]:
    """Get the list of Fluxer role IDs that are accepted for a signup category.

    Returns role_id as a single-item list if role_ids_accepted is empty,
    otherwise returns role_ids_accepted.
    """
    for role_def in roles_config.get("signup_roles", []):
        if role_def["key"] == role_key:
            accepted = role_def.get("role_ids_accepted", [])
            if accepted:
                return [str(rid) for rid in accepted]
            role_id = role_def.get("role_id", "")
            if role_id:
                return [str(role_id)]
            return []
    return []


__all__ = [
    "render_event_post",
    "get_all_reaction_emoji",
    "emoji_to_role_key",
    "role_key_to_emoji",
    "get_accepted_role_ids",
]
