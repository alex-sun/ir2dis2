# iRacing Discord Bot - Feature Documentation

## 1. Purpose
A Discord bot that **tracks iRacing race results** for selected drivers and **posts them automatically** to a designated Discord channel. Users manage tracking with **three slash commands** preserved from the reference project:
- `/lastrace customer_id:<id>` — on-demand: show the latest official race result for a specific iRacing member.
- `/setchannel channel:<#channel>` — admin-only: set the channel where auto-posted results will appear.
- `/trackmember customer_id:<id>` — add a member (by iRacing Customer ID) to the bot's tracking list for the current server.

The bot operates in the background, polling iRacing for new finished races for tracked members and posting a summary when a new result appears.

## 2. In-Scope Features
- **Slash commands** (exact names/params as above).
- **Per-server tracking lists** (each Discord guild maintains its own set of tracked members).
- **Auto-posting**: when a tracked member finishes an official race, post a single digest message to the configured channel.
- **De-duplication**: a race result is posted **once** per guild+member.
- **Persistence**: tracking lists, configured channel, and last-posted race IDs survive restarts (SQLite file).

## 3. Out-of-Scope (MVP)
- Real-time lap-by-lap telemetry, live "race started" notifications, or deep analytics.
- Cross-platform messaging (Telegram/Slack/etc.).
- User authentication flows beyond Discord bot identity.
- Arbitrary iRacing data browsing beyond what's required to post latest results.
- Moderation systems, permissions beyond what's needed for `/setchannel` (admin).

## 4. Users & Roles
- **Server Admins** — can run all commands; `/setchannel` requires guild admin permission.
- **Regular Members** — can use `/lastrace` to fetch last result for any customer_id; may be allowed to use `/trackmember` (policy is configurable but default is **allow**).

## 5. Command Behaviors (UX)
### `/trackmember customer_id:<id>`
- Adds the member to this guild's tracking list.
- If already tracked, respond with an idempotent confirmation.
- Success message example: "Member **123456** is now being tracked in this server."

### `/setchannel channel:<#channel>` (admin-only)
- Saves the provided channel as the **results channel** for this guild.
- Confirms success; warns if the bot cannot send messages to that channel.

### `/lastrace customer_id:<id>`
- Responds with the **most recent official race** for that member (if any), including at least:
  - Series or event name
  - Track name
  - Field size (if available)
  - Start position, finish position
  - iRating delta and championship points (if available)
  - Timestamp of the session (UTC or guild-localized)

## 6. Auto-Posting
A background task runs periodically (e.g., every 60 seconds):
- For each tracked member in each guild:
  - Query iRacing for **recent official races**.
  - If the most recent subsession differs from the stored `last_published_subsession_id`, publish a formatted summary to the configured channel and update the stored value.
- If no results channel is set for a guild, skip posting for that guild and log a warning.

## 7. Message Formatting
Use clear, concise summaries (text or embed). Example:
> **Ivan Ivanov** finished **P5 / 20** in **GT3 Challenge** at **Spa-Francorchamps**. iRating: **+42**, Points: **85**. (2025‑08‑17 14:30Z)

If a datum is unavailable, omit it gracefully.

## 8. Data Model (Conceptual)
- **GuildConfig**: `{ guild_id, results_channel_id }`
- **TrackedMember**: `{ guild_id, customer_id }`
- **LastPublished**: `{ guild_id, customer_id, subsession_id }`

## 9. Reliability & Safety
- Network errors and API outages are **handled gracefully**; the bot retries later.
- Discord permission errors are logged with actionable hints.
- Secrets (Discord token, iRacing credentials) are stored in **env vars**, never in code or logs.

## 10. Non-Functional
- **Containerized**: runs entirely in Docker.
- **Portability**: no host Python required.
- **Observability**: structured logs to stdout; poll interval configurable via env.

# iRacing Data API – Practical Integration Notes

> This guide summarizes what the bot needs from iRacing's "/data" API to find and post **latest official race results** for a member.

## 1) Authentication
- Authenticate against **`https://members-ng.iracing.com/auth`** with your iRacing credentials (email + password).
- On success you receive cookies/tokens used for subsequent **`/data/*`** requests.
- If your account uses 2FA, enable **Legacy Read Only Authentication** in account settings to allow script access to the Data API without a second factor (until OAuth is available).
- Keep the session cookie in an HTTP client session; refresh/re-login on **401 Unauthorized**.

## 2) Endpoints You'll Use Most
### a) **Recent races for a member**
- **`GET /data/stats/member_recent_races?cust_id={customer_id}`**
- Returns the **last 10 official races** for the member. Use the first entry as the "latest finished race".

### b) **Session/Subsession results (details)**
- **`GET /data/results/get?subsession_id={subsession_id}`**
- Returns result details for a subsession (race), including positions, field size, track, series, etc.
- Call this **only when** you need fields not present in the "recent races" response (to reduce load).

> Other useful lookups exist (cars, tracks, series), but the two endpoints above are sufficient for MVP posting.

## 3) Polling Strategy
- Poll **only** the tracked members, on a configurable interval (e.g., 60s).
- Cache/store the **last published `subsession_id`** per guild+member to avoid duplicate posts.
- Stagger requests across members to avoid burst traffic.

## 4) Error Handling & Backoff
- Treat network and 5xx as transient; retry with jittered backoff.
- Treat 401 as "session expired"; attempt re-auth once, then log and continue.
- Rate limiting: if observed, slow down polling interval and log a warning.

## 5) Data Hygiene
- Customer IDs are integers (`cust_id`). Accept them verbatim from commands.
- Timestamps from API are typically UTC; format consistently in messages.
- Be robust to missing fields; prefer omission over "None/NaN" text.

## 6) Security
- Do **not** log credentials or raw cookies.
- Keep secrets in env vars; never commit them.
- Rotate credentials when staff changes.

# LLM Engineer Playbook (You Are the Developer)

> You will write the bot in **Python** with **discord.py 2.x** (slash commands via `app_commands`), use **aiohttp** for iRacing, and **SQLite** for persistence — all inside **Docker**. No host Python.

## Golden Rules
1. **Keep commands exact**: `/lastrace customer_id:<id>`, `/setchannel channel:<#channel>`, `/trackmember customer_id:<id>`.
2. **Everything runs in Docker**. No `pip` on the host.
3. **Idempotent & resilient**: commands don't crash; background task recovers on errors.
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

# Implementation Roadmap

Each stage ends with a **test & commit** gate. Keep changes small and shippable.

## Stage 0 — Repo & Bootstrap (commit: init)
- Create repo with `bootstrap/` content (copy & adapt).
- Fill `.env` from `.env.example`.
- Build & run container (bot will just print "starting" until code exists).

## Stage 1 — Slash Command Skeletons (commit: feat/commands-skeleton)
- Wire up `discord.py` app with intents and `/lastrace`, `/setchannel`, `/trackmember` declarations.
- Bot connects and responds with placeholder messages.
- **Test**: run container, verify commands appear and respond.

## Stage 2 — SQLite Layer (commit: feat/db)
- Implement schema:
  - `guild_config(guild_id PRIMARY KEY, channel_id)`
  - `tracked_member(guild_id, customer_id, PRIMARY KEY(guild_id, customer_id))`
  - `last_published(guild_id, customer_id, subsession_id, PRIMARY KEY(guild_id, customer_id))`
- Add helpers and basic unit tests.
- **Test**: add/remove tracked rows; set/get channel; upsert last_published.

## Stage 3 — iRacing Auth & Recent Races (commit: feat/api-recent)
- Implement login (cookies) and `GET /data/stats/member_recent_races?cust_id=...`.
- Implement `/lastrace` to fetch & format the latest official race.
- **Test**: manual `/lastrace` on a known `customer_id` with realistic payload samples.

## Stage 4 — Subsession Details (commit: feat/api-subsession)
- Implement `GET /data/results/get?subsession_id=...` for missing fields (track, field size, etc.).
- Extend formatter to include optional fields if available.
- **Test**: unit tests with sample subsession payloads.

## Stage 5 — Background Poller (commit: feat/poller)
- Implement `tasks.loop` poller with dedupe via `last_published`.
- Respect `POLL_INTERVAL_SECONDS`. Handle 401 re-login.
- **Test**: force a known subsession id change and verify **single** post, then no duplicates.

## Stage 6 — Hardening & Docs (commit: chore/hardening docs)
- Add structured logging, exception guards, graceful shutdown.
- Fill `README.md` with run instructions; verify Docker-only operation.
- **Test**: run for several hours against a test `customer_id`, confirm stability.

## Optional Stage 7 — Nice-to-Haves
- Slash command `/listtracked`.
- `/help` embed with usage.
- Per-guild poll interval.
- Slash command permissions refinements.

— Generated 2025-08-17