# LLM Engineer Playbook (You Are the Developer)

> You will write the bot in **Python** with **discord.py 2.x** (slash commands via `app_commands`), use **aiohttp** for iRacing, and **SQLite** for persistence — all inside **Docker**. No host Python.

## Golden Rules
1. **Keep commands exact**: `/lastrace customer_id:<id>`, `/setchannel channel:<#channel>`, `/trackmember customer_id:<id>`.
2. **Everything runs in Docker**. No `pip` on the host.
3. **Idempotent & resilient**: commands don’t crash; background task recovers on errors.
4. **No secrets in code or logs**. Use env vars exclusively.
5. **Commit small, reviewable increments** tied to roadmap stages.

## Project Layout (no code yet)
```
/app
  ├─ src/
  │   ├─ bot.py                 # entrypoint (main)
  │   ├─ db.py                  # SQLite/aiosqlite helpers
  │   ├─ iracing_api.py         # auth + endpoints
  │   ├─ models.py              # dataclasses for typed payloads
  │   └─ settings.py            # env parsing (pydantic or os.getenv)
  ├─ tests/                     # pytest
  ├─ docker/Dockerfile
  ├─ docker-compose.yml
  ├─ requirements.txt
  ├─ .env.example
  └─ README.md
```

## Minimum Technical Choices
- **discord.py 2.x** (slash commands via `discord.app_commands`).
- **aiohttp** for async HTTP (`ClientSession`, timeouts, cookie jar).
- **aiosqlite** or `sqlite3` via `asyncio.to_thread`.
- **pytest** for unit tests (parsers, DB functions, message formatting).

## Slash Commands (Implementation Notes)
- Register `/lastrace` and `/trackmember` with required integer option `customer_id`.
- Register `/setchannel` with required channel option `channel` (type: text channel).
- Gate `/setchannel` with `administrator` (Discord permission).
- Respond using ephemeral replies for confirmations; use embeds for race summaries.

## Background Poller
- Use `discord.ext.tasks.loop(seconds=POLL_INTERVAL)` and start it in `on_ready`.
- For each guild: load tracked members; for each member: fetch recent races → compare newest `subsession_id` → post if new → save.
- Do not block the event loop (no long sync I/O).

## Logging
- Use Python `logging` with INFO default; DEBUG for development.
- Log one line per posted result: `guild=<id> member=<id> subsession=<id>`.
- On failures, include context but never secrets.

## Git & Commits
- Commit after each roadmap checkpoint with conventional messages, e.g.:
  - `feat: add slash commands skeleton`
  - `feat(api): member_recent_races + session results`
  - `feat(db): sqlite schema and helpers`
  - `feat(poller): posting loop with dedupe`
  - `docs: usage and docker instructions`
- Keep PRs focused (≤300 lines diff) to aid review.

## Testing
- Unit-test: message formatter (given sample payloads), DB helpers (using `:memory:`), API helpers with faked responses.
- Manual E2E: test server, add one known `customer_id`, set channel, verify a post using a known recent race.

## Docker
- The container must start the bot with **only** `DISCORD_TOKEN`, `IRACING_EMAIL`, `IRACING_PASSWORD`. Optional:
  - `POLL_INTERVAL_SECONDS` (default 60)
  - `LOG_LEVEL` (default INFO)
  - `SQLITE_DB_PATH` (default `/app/data/iresults.db`)

## Done Means
- Commands registered, permissions correct.
- Poller posts exactly once per race per guild+member.
- Clean shutdown, session closed, no unhandled exceptions in logs.
