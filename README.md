# Bragi Bot Skeleton

Template framework for building new bots in the [Bragi](https://github.com/the-alphabet-cartel/bragi) bot infrastructure for [The Alphabet Cartel](https://fluxer.gg/yGJfJH5C).

---

## What This Is

This skeleton provides a fully charter-compliant starting point for new Bragi bots. Every file follows the [Clean Architecture Charter](https://github.com/the-alphabet-cartel/bragi/blob/main/docs/standards/charter.md) and is ready for find-and-replace customisation.

**Included out of the box:**

- Three-layer config stack (JSON → `.env` → Docker Secrets) — Rules #4 / #7
- Factory function pattern for all managers — Rule #1
- Dependency injection throughout — Rule #2
- Colorized logging with SUCCESS level — Rule #9
- Multi-stage Dockerfile with Python 3.12 + venv — Rule #10
- Pure Python entrypoint with tini + PUID/PGID — Rule #12
- Example handler with dedup guard (fluxer-py fires events twice)
- GitHub Actions CI/CD workflow for GHCR
- File version headers on all source files — Rule #6

---

## Quick Start: Creating a New Bot

### 1. Copy the skeleton

```
cp -r skeleton/ ratatoskr/
```

### 2. Find and replace placeholders

Search across all files and replace:

| Placeholder | Replace With | Example |
|---|---|---|
| `ratatoskr` | Your bot's name (lowercase, hyphenated) | `portia-bot` |
| `RATATOSKR` | Your bot's env var prefix (SCREAMING_SNAKE) | `PORTIA` |

**Files that need replacement:**

- `src/main.py`
- `src/managers/config_manager.py`
- `src/managers/logging_config_manager.py`
- `src/handlers/example_handler.py`
- `src/config/ratatoskr_config.json` ← also rename this file
- `docker-entrypoint.py`
- `docker-compose.yml`
- `.env.template`
- `Dockerfile`
- `requirements.txt`
- `secrets/README.md`
- `.github/workflows/build.yml`
- This `README.md`

### 3. Rename the config file

```
mv src/config/ratatoskr_config.json src/config/your-bot-name_config.json
```

### 4. Add your bot logic

- Rename or replace `src/handlers/example_handler.py` with your handler(s)
- Add bot-specific managers in `src/managers/`
- Add bot-specific config sections to the JSON config file
- Add bot-specific env vars to `.env.template` and `config_manager.py`
- Update `src/main.py` to import and wire up your handlers

### 5. Set up secrets

```
mkdir -p secrets
printf 'your-token-here' > secrets/ratatoskr_fluxer_token
chmod 600 secrets/ratatoskr_fluxer_token
```

### 6. Create a `.env`

```
cp .env.template .env
# Edit .env — set GUILD_ID and any bot-specific values
```

### 7. Deploy

```bash
# Create host directories on Bragi
mkdir -p /opt/bragi/bots/ratatoskr/logs
mkdir -p /opt/bragi/bots/ratatoskr/data

# Ensure the bragi network exists
docker network create bragi 2>/dev/null || true

# Build and run
docker compose up -d --build
```

---

## Project Structure

```
ratatoskr/
├── docker-compose.yml            ← Container orchestration
├── Dockerfile                    ← Multi-stage build (Rule #10)
├── docker-entrypoint.py          ← PUID/PGID + tini (Rule #12)
├── .env.template                 ← Config reference (committed)
├── requirements.txt              ← fluxer-py + httpx
├── images/
│   └── (bot profile picture)     ← Add your bot's PFP here
├── secrets/
│   ├── README.md                 ← Setup instructions (committed)
│   └── ratatoskr_fluxer_token   ← Bot token (gitignored)
└── src/
    ├── main.py                   ← Entry point + event dispatchers
    ├── config/
    │   └── ratatoskr_config.json ← JSON defaults (Rule #4)
    ├── handlers/
    │   └── example_handler.py    ← Example handler (replace me)
    └── managers/
        ├── config_manager.py           ← Three-layer config (Rule #7)
        └── logging_config_manager.py   ← Colorized logging (Rule #9)
```

---

## Architecture Notes

### Handler Pattern

fluxer-py's Cog system is broken (v0.3.1). Bragi bots use plain handler classes:

```python
class MyHandler:
    def __init__(self, bot, config_manager, logging_manager):
        self.bot = bot
        self.log = logging_manager.get_logger("my_handler")

    async def handle_message(self, message):
        ...
```

Each handler is called from a **single dispatcher** in `main.py` because fluxer-py only supports one registered handler per event type.

### Event Deduplication

fluxer-py fires every gateway event twice. The example handler includes a dedup guard pattern — copy it into every handler that processes events.

### REST vs Gateway

Some operations only work through direct HTTP calls, others only through fluxer-py gateway methods. See [fluxer-py Quirks & API Reference](https://github.com/the-alphabet-cartel/bragi/blob/main/docs/standards/fluxer-py_quirks.md) for full details.

---

## Charter Compliance

| Rule | Status |
|------|--------|
| #1 Factory Functions | ✅ All managers use `create_*()` |
| #2 Dependency Injection | ✅ All managers accept deps via constructor |
| #3 Additive Development | ✅ |
| #4 JSON Config + Secrets | ✅ Three-layer stack |
| #5 Resilient Validation | ✅ Fallbacks with logging |
| #6 File Versioning | ✅ All files versioned |
| #7 Config Hygiene | ✅ Secrets/env/JSON separated |
| #8 Real-World Testing | ⬜ Test against live Fluxer instance |
| #9 LoggingConfigManager | ✅ Standard colorization |
| #10 Python 3.12 + Venv | ✅ Multi-stage Docker build |
| #11 File System Tools | ✅ |
| #12 Python Entrypoint + tini | ✅ PUID/PGID support |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [fluxer-py](https://github.com/akarealemil/fluxer.py) | Fluxer bot library |
| [httpx](https://www.python-httpx.org/) | HTTP client for REST API calls |

---

**Built with care for chosen family** 🏳️‍🌈
