# Ratatoskr — Event Scheduling Bot for JTF Drauger

## Design Specification v1.0

**Bot Name:** Ratatoskr  
**Namesake:** The magical squirrel messenger that runs up and down Yggdrasil  
**Ecosystem:** Bragi Bot Infrastructure  
**Community:** Joint Task Force Drauger (Arma 3 MilSim)  
**Platform:** Fluxer (via fluxer-py)  
**Repository:** `the-alphabet-cartel/ratatoskr` (submodule under Bragi)

---

## 1. Purpose

Ratatoskr is an event scheduling and attendance tracking bot that replicates the core functionality of the Apollo Discord Calendar bot within the Fluxer platform. It enables Command Staff to create MilSim Operations (events), and allows members to RSVP by reacting with role-specific emoji. The bot enforces role-based signup restrictions, maintains a live attendance roster, and handles event lifecycle management including reminders and automatic cleanup.

---

## 2. Architecture

### 2.1 Bragi Ecosystem Pattern

Ratatoskr follows the established Bragi bot architecture:

- **Handler classes** — Pure logic, no event registration (learned from Prism: fluxer-py only supports one handler per event type)
- **Single dispatcher** in `main.py` — Routes `on_message` and `on_reaction_add`/`on_reaction_remove` events
- **Three-layer configuration** — JSON defaults → environment variables → Docker Secrets
- **Structured logging** via `LoggingConfigManager`
- **Docker containerization** with unified `docker-compose` deployment
- **Git submodule** under Bragi repository

### 2.2 Repository Structure

```
ratatoskr/
├── src/
│   ├── main.py                    # Entry point + event dispatcher
│   ├── config/
│   │   ├── default_config.json    # Default configuration values
│   │   └── roles_config.json      # Role-to-emoji mapping (hot-reloadable)
│   ├── handlers/
│   │   ├── event_create.py        # DM-based event creation flow
│   │   ├── event_manage.py        # !edit, !delete command handling
│   │   ├── reaction_handler.py    # Reaction add/remove + role enforcement
│   │   ├── channel_guard.py       # Delete non-event messages from event channel
│   │   └── reminder.py            # 15-minute pre-event DM reminders
│   ├── managers/
│   │   ├── config_manager.py      # Three-layer config loading
│   │   ├── logging_config_manager.py
│   │   └── database_manager.py    # SQLite interface
│   ├── models/
│   │   ├── event.py               # Event data model
│   │   └── signup.py              # Signup/attendance data model
│   └── utils/
│       ├── time_parser.py         # Natural language → datetime (24hr)
│       └── event_formatter.py     # Renders event embed/message text
├── .env.template
├── Dockerfile
├── requirements.txt
├── README.md
└── docs/
    └── design.md                  # This document
```

### 2.3 Data Flow Diagram

```
User types "!event"
        │
        ▼
  ┌─────────────┐     ┌──────────────────┐
  │ main.py     │────>│ event_create.py  │
  │ dispatcher  │     │ DM conversation  │
  └─────────────┘     └────────┬─────────┘
        │                      │
        │               Bot DMs user for:
        │               • Event Name
        │               • Description
        │               • Event Time (24hr)
        │                      │
        │                      ▼
        │              ┌─────────────────┐
        │              │ event_formatter │
        │              │ builds message  │
        │              └───────┬─────────┘
        │                      │
        │                      ▼
        │              ┌────────────────┐
        │              │ Posts to event │
        │              │ channel + adds │
        │              │ role reactions │
        │              └───────┬────────┘
        │                      │
        │                      ▼
        │              ┌─────────────────┐
        │              │ database_mgr    │
        │              │ saves to SQLite │
        │              └─────────────────┘
        │
  on_reaction_add / on_reaction_remove
        │
        ▼
  ┌───────────────────┐
  │ reaction_handler  │
  │ • Check user role │
  │ • Enforce 1 role  │
  │ • Update roster   │
  │ • Edit message    │
  └───────────────────┘
```

---

## 3. Configuration

### 3.1 `.env.template`

```bash
# ============================================================================
# Ratatoskr Bot — Environment Configuration
# ============================================================================
# TOKEN loaded via Docker Secret: /run/secrets/ratatoskr_token

# Channel where events are POSTED (not where commands are typed)
RATATOSKR_EVENT_CHANNEL_ID=

# Guild ID for the JTF Drauger server
RATATOSKR_GUILD_ID=

# Role ID that gates event creation
RATATOSKR_COMMAND_STAFF_ROLE_ID=

# Command prefix
COMMAND_PREFIX=!

# Log level
LOG_LEVEL=INFO

# SQLite database path (inside container, mounted volume)
RATATOSKR_DB_PATH=/data/ratatoskr.db
```

### 3.2 `roles_config.json`

This file is the heart of the role-to-emoji mapping. It is designed to be edited as roles are added/removed from the server.

```json
{
    "_comment": "Role-to-emoji mapping for event signups. Order determines display order in event posts.",
    "_instructions": "emoji: Unicode emoji or custom emoji ID. role_id: Fluxer role snowflake. label: Display name in event post.",
    "signup_roles": [
        {
            "key": "operator",
            "label": "Operator",
            "emoji": "🇦",
            "role_id": "",
            "max_slots": null
        },
        {
            "key": "specialist",
            "label": "Specialist",
            "emoji": "🇧",
            "role_id": "",
            "max_slots": null
        },
        {
            "key": "element_lead",
            "label": "EL+TL",
            "emoji": "🇨",
            "role_id": "",
            "role_ids_accepted": [],
            "max_slots": null
        },
        {
            "key": "recruit",
            "label": "Recruit",
            "emoji": "🇩",
            "role_id": "",
            "max_slots": null
        },
        {
            "key": "214soar",
            "label": "214 SOAR",
            "emoji": "🇪",
            "role_id": "",
            "max_slots": null
        },
        {
            "key": "tacp",
            "label": "TACP",
            "emoji": "🇫",
            "role_id": "",
            "max_slots": null
        },
        {
            "key": "goblin",
            "label": "Goblin",
            "emoji": "🇬",
            "role_id": "",
            "max_slots": null
        },
        {
            "key": "hq",
            "label": "HQ",
            "emoji": "🇭",
            "role_id": "",
            "max_slots": null
        }
    ],
    "declined": {
        "label": "Declined",
        "emoji": "❌"
    }
}
```

**Design notes:**
- `role_id` is a single string for the typical case (one role maps to one reaction)
- `role_ids_accepted` is an optional array for categories that accept multiple roles (e.g., EL+TL might accept both `Element Lead` and `Team Lead` role IDs)
- `max_slots` is nullable for future capacity limits per role
- `emoji` can be a Unicode emoji string or a Fluxer custom emoji ID
- The `declined` entry has no role restriction — anyone with any signup role can decline
- Array order determines display order in the event post

### 3.3 `default_config.json`

```json
{
    "event_cleanup_hours": 24,
    "reminder_minutes_before": 15,
    "time_format_display": "%A, %B %d, %Y %H:%M",
    "timezone": "America/New_York",
    "delete_command_messages": true,
    "delete_non_event_messages": true,
    "event_post_color": null
}
```

---

## 4. Database Schema (SQLite)

### 4.1 `events` Table

```sql
CREATE TABLE events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      TEXT NOT NULL UNIQUE,       -- Fluxer message snowflake of the event post
    channel_id      TEXT NOT NULL,              -- Channel where event was posted
    creator_id      TEXT NOT NULL,              -- User who created the event
    title           TEXT NOT NULL,
    description     TEXT,
    event_time      TEXT NOT NULL,              -- ISO 8601 UTC
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    reminder_sent   INTEGER NOT NULL DEFAULT 0, -- 0=no, 1=yes
    expired         INTEGER NOT NULL DEFAULT 0  -- 0=active, 1=expired/cleaned up
);
```

### 4.2 `signups` Table

```sql
CREATE TABLE signups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL,              -- Fluxer user snowflake
    display_name    TEXT NOT NULL,              -- Nickname at time of signup (includes rank prefix)
    role_key        TEXT NOT NULL,              -- Key from roles_config (e.g., "operator", "declined")
    signed_up_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(event_id, user_id)                  -- One signup per user per event
);
```

**Key constraint:** `UNIQUE(event_id, user_id)` — a user can only have one signup per event. If they switch reactions (e.g., from their role to Declined), the existing row is updated via `INSERT OR REPLACE`.

---

## 5. Feature Specifications

### 5.1 Event Creation (`!event`)

**Trigger:** User with `Command Staff` role types `!event` in any channel.

**Flow:**

1. Bot deletes the `!event` message from the channel
2. Bot sends a DM to the user initiating the creation wizard:
   - **Step 1:** "What is the name of this operation?"
   - **Step 2:** "Provide a description for the operation:"
   - **Step 3:** "When is the operation? (Use 24-hour format, e.g., 'Sunday, March 1, 2026 14:00')"
3. User responds to each prompt in DM
4. Bot parses the time using natural language processing (24-hour format enforced)
5. Bot posts the formatted event to the configured `RATATOSKR_EVENT_CHANNEL_ID`
6. Bot adds all configured emoji reactions to the posted message (in order from `roles_config.json`, then the declined emoji)
7. Bot saves the event to SQLite
8. Bot DMs the creator: "Operation posted successfully! [link to message]"

**Permission check:** If the user does NOT have `Command Staff` role, the `!event` message is still deleted (channel guard), but no DM is sent. Silently ignored.

**Timeout:** If the user doesn't respond to a DM prompt within 5 minutes, the creation is cancelled and the user is notified.

### 5.2 Event Post Format

The event message posted by the bot follows this structure:

```
═══════════════════════════════════════
📋 Operation Enduring West — Phase 11 & Phase 12

NDI have held this region's international airport and heavily
fortified it. They know we're coming. This part of the operation
is going to be 2 phases, 11 and 12.
11: Secure the area around the international airport...
12: Assault and secure the international airport...

⏰ Time
Sunday, March 01, 2026 14:00
⏳ in 2 days

───────────────────────────────────────
🇦 Operator (2)
  [PFC] Redcoat
  [PFC] Kebab

🇧 Specialist (4)
  [Cpl] Steel Beater
  [PFC] Kawkakodza
  [HA] Charlie
  [LCpl] Papa_PistOla

🇨 EL+TL (4)
  [Sgt] Wyvern
  [Sgt] CyBer
  [Cpl] Poet
  [LCpl] Eta

🇩 Recruit (2)
  [Pvt] Rogue
  [Pvt] Brinks

🇪 214 SOAR (3)
  [WO1] Krazy
  [CPT] Demon
  [2ndLt] SnazzyDuckling

🇫 TACP (1)
  [SrA] Solved

🇬 Goblin (2)
  [SSA] Banks
  [SA] DeltaCommander

🇭 HQ
  —

❌ Declined (1)
  [HA] Saiun

Created by [Maj]Beserk
═══════════════════════════════════════
```

**Rendering notes:**
- The countdown ("in 2 days") is calculated at post time and re-calculated on each edit
- Role sections with zero signups display a dash (—)
- The count in parentheses updates with each signup/withdrawal
- Display names are pulled from the user's server nickname (which includes rank prefix)

### 5.3 Reaction Handling

**On Reaction Add:**

1. Ignore reactions from bots
2. Ignore reactions on messages that aren't tracked events (check `events` table by `message_id`)
3. Look up which `role_key` the emoji maps to (from `roles_config.json`)
4. If emoji is not in config, remove the reaction and stop
5. **If the reaction is for a role category (not Declined):**
   a. Fetch the user's server roles via `guild.fetch_member(user_id)`
   b. Check if the user holds the role(s) specified by that category's `role_id` / `role_ids_accepted`
   c. If the user does NOT have the required role → remove the reaction, stop
   d. If the user DOES have the required role → proceed to signup
6. **If the reaction is Declined:**
   a. Any user with at least one of the signup roles can decline — no specific role check needed
   b. Users with Command Staff role (only) and no signup role cannot react at all
7. **Process signup:**
   a. Remove any previous reaction by this user on this event message (they can only hold one)
   b. `INSERT OR REPLACE` into `signups` table
   c. Fetch the user's display name (nickname) from the server
   d. Re-render the event message with updated attendance lists
   e. Edit the event message in place

**On Reaction Remove:**

1. Same event check as above
2. Look up the user's signup in the database
3. If found and matches the removed emoji's role_key → delete the signup row
4. Re-render and edit the event message

**Edge case: User switches reactions**

When a user adds a new reaction (e.g., switching from Specialist to Declined):
- `on_reaction_add` fires for the new reaction
- The handler removes the old reaction programmatically (which fires `on_reaction_remove`)
- The handler must distinguish between "bot removed a reaction" and "user removed a reaction"
- Solution: Track pending reaction removals in an in-memory set. If a removal matches a pending entry, skip the database/re-render step.

### 5.4 Channel Guard

The event channel (`RATATOSKR_EVENT_CHANNEL_ID`) is kept clean:

- **Any message not from the bot** is deleted immediately
- This includes `!event` commands typed in the event channel
- This includes casual messages, questions, etc.
- **Bot messages that are event posts** are preserved
- **Implementation:** In `on_message`, if `message.channel.id == RATATOSKR_EVENT_CHANNEL_ID` and `message.author.id != bot.user.id`, delete the message

### 5.5 Event Edit (`!edit`)

**Trigger:** `!edit <event_id>` — where `event_id` is the database row ID or the message ID

**Permission:** Must be the original creator OR have `Command Staff` role

**Flow:**

1. Bot deletes the command message
2. Bot DMs the user with current event details and prompts:
   - "What would you like to edit? (title / description / time)"
3. User selects a field
4. Bot prompts for new value
5. Bot updates the database, re-renders and edits the event message

### 5.6 Event Delete (`!delete`)

**Trigger:** `!delete <event_id>`

**Permission:** Must be the original creator OR have `Command Staff` role

**Flow:**

1. Bot deletes the command message
2. Bot DMs the user: "Are you sure you want to delete 'Operation Name'? (yes/no)"
3. If confirmed:
   a. Delete the event message from the channel
   b. Delete all signup rows from the database
   c. Mark event as expired in the database
   d. DM confirmation: "Operation deleted."

### 5.7 Reminders

A background task runs every 60 seconds checking for events where:
- `event_time` is within 15 minutes from now
- `reminder_sent` is 0

When found:
1. Query all signups for the event (excluding "declined")
2. DM each signed-up user: "⏰ Reminder: **Operation Name** begins in 15 minutes!"
3. Set `reminder_sent = 1` on the event

### 5.8 Event Expiry / Cleanup

A background task runs every 15 minutes checking for events where:
- `event_time` is more than 24 hours in the past
- `expired` is 0

When found:
1. Delete the event message from the channel
2. Mark `expired = 1` in the database
3. (Signup data is retained for historical reference)

---

## 6. Event Dispatcher Design

Since fluxer-py only supports one handler per event type, `main.py` routes all events:

```python
@bot.event
async def on_message(message: fluxer.Message) -> None:
    if message.author.bot:
        return

    # Channel guard — delete non-bot messages in event channel
    if str(message.channel.id) == config.get("RATATOSKR_EVENT_CHANNEL_ID"):
        try:
            await message.delete()
        except Exception:
            pass
        # Still process commands even if in event channel
        # (the command message is already deleted above)

    # Command routing
    if message.content.startswith(prefix):
        cmd = message.content[len(prefix):].strip().split()[0].lower()
        if cmd == "event":
            await event_create_handler.handle(message)
        elif cmd == "edit":
            await event_manage_handler.handle_edit(message)
        elif cmd == "delete":
            await event_manage_handler.handle_delete(message)
        return

    # Non-command, non-event-channel messages — ignore
    # (channel guard already handled event channel cleanup above)


@bot.event
async def on_reaction_add(reaction, user) -> None:
    # NOTE: Actual signature TBD — needs empirical testing
    # May be on_raw_reaction_add with payload dict
    if user.bot:
        return
    await reaction_handler.handle_add(reaction, user)


@bot.event
async def on_reaction_remove(reaction, user) -> None:
    # NOTE: Same caveat as above
    if user.bot:
        return
    await reaction_handler.handle_remove(reaction, user)
```

**Critical note:** The `on_reaction_add` / `on_reaction_remove` event signatures are **unconfirmed** in fluxer-py. This is the #1 item to test before coding begins. PerpetualPossum's rolebot confirms these events exist, but the exact parameter shapes may differ from discord.py.

---

## 7. Natural Language Time Parsing

Requirements:
- Input: Natural language with 24-hour time ("Sunday, March 1, 2026 14:00" or "next Sunday at 19:30" or "March 1 14:00")
- Output: Python `datetime` in configured timezone
- Library: `python-dateutil` (parsedate with fuzzy matching) + custom 24-hour enforcement
- Validation: Reject times in the past, reject unparseable input with a helpful error DM

Example acceptable inputs:
- `Sunday, March 1, 2026 14:00`
- `March 1 14:00`
- `2026-03-01 14:00`
- `next Sunday 19:30`
- `tomorrow 20:00`

---

## 8. Dependencies

```
fluxer-py           # Fluxer API wrapper
python-dateutil     # Natural language date parsing
aiosqlite           # Async SQLite for non-blocking DB ops
pytz                # Timezone handling
```

---

## 9. Docker Configuration

### `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
CMD ["python", "-m", "src.main"]
```

### `docker-compose.yml` (addition to Bragi unified compose)

```yaml
  ratatoskr:
    build:
      context: ./ratatoskr
      dockerfile: Dockerfile
    container_name: ratatoskr
    restart: unless-stopped
    env_file:
      - ./ratatoskr/.env
    secrets:
      - ratatoskr_token
    volumes:
      - ratatoskr_data:/data
    networks:
      - bragi

volumes:
  ratatoskr_data:

secrets:
  ratatoskr_token:
    file: ./secrets/ratatoskr_token.txt
```

---

## 10. Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| `on_reaction_add`/`on_reaction_remove` events untested in fluxer-py | **HIGH** | Test before coding. PerpetualPossum's rolebot confirms existence. Fallback: poll message reactions via HTTP API on interval. |
| `message.delete()` may not exist or work differently | **MEDIUM** | Test alongside reaction events. Fallback: use HTTP DELETE via bot client. |
| `message.edit()` may behave differently | **MEDIUM** | Test. Fallback: delete + repost (loses reactions — worst case). |
| DM sending may not work as expected | **MEDIUM** | Already partially confirmed via Prism testing. Needs DM channel creation test. |
| Reaction removal by bot triggers `on_reaction_remove` causing infinite loop | **LOW** | In-memory pending-removal set to distinguish bot actions from user actions. |
| fluxer-py rate limiting on rapid reaction adds | **LOW** | Queue re-renders with debounce (100ms delay before editing message). |

---

## 11. Testing Checklist (Pre-Development)

These must be confirmed on the JTF Drauger Fluxer server before building:

- [ ] `on_reaction_add` event fires and provides user + emoji info
- [ ] `on_reaction_remove` event fires and provides user + emoji info
- [ ] `message.add_reaction(emoji)` works for Unicode emoji
- [ ] `message.delete()` works
- [ ] `message.edit(content=...)` works and preserves reactions
- [ ] Bot can send DMs to users (`user.send()` or equivalent)
- [ ] Bot can fetch a user's server nickname (display name with rank prefix)
- [ ] Regional indicator emoji (🇦🇧🇨 etc.) render correctly as reactions in Fluxer

---

## 12. Implementation Phases

### Phase 1: Foundation + Proof of Concept
- Repository scaffolding (matching Bragi skeleton)
- Config managers, logging, database schema
- Reaction API testing harness
- Channel guard (delete non-bot messages)

### Phase 2: Event Creation
- `!event` command + DM wizard flow
- Time parsing
- Event post formatting + rendering
- Emoji reaction seeding on new events

### Phase 3: Attendance Tracking
- `on_reaction_add` handler with role enforcement
- `on_reaction_remove` handler
- Message re-rendering on signup changes
- Reaction switching logic

### Phase 4: Lifecycle Management
- `!edit` command
- `!delete` command
- Background task: 15-minute reminders
- Background task: 24-hour expiry cleanup

### Phase 5: Hardening
- Error handling for all fluxer-py edge cases
- Debounced message edits
- Graceful restart (re-sync reactions from existing messages)
- Documentation + deploy

---

*Document version: 1.0*  
*Last updated: 2026-02-27*  
*Author: PapaBearDoes*
