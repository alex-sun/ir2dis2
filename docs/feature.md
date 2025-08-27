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

# iRacing Data API – Practical Integration (iracingdataapi Library)

> This guide shows how to use the **`iracingdataapi`** Python library to interact with iRacing's Data API. The library handles authentication, retries, rate limiting, and data parsing automatically - no need to work with raw API endpoints directly.

## 1) Library Setup & Authentication
The bot uses the `irDataClient` class from `iracingdataapi` to manage API access:

```python
from iracingdataapi.client import irDataClient

# Initialize client with credentials (from env vars in production)
client = irDataClient(
    username=os.getenv("IRACING_USERNAME"),
    password=os.getenv("IRACING_PASSWORD"),
    silent=True  # Disable debug logging in production
)
```

- The library handles **automatic re-login** on 401 Unauthorized responses.
- For 2FA accounts: Enable **Legacy Read Only Authentication** in iRacing settings (required until OAuth support is added).
- Credentials should always come from environment variables - never hardcode them.

## 2) Key Methods for Race Results
The library provides wrapper methods for exactly the endpoints needed for MVP functionality:

### a) **Recent Races for a Member**
Use `stats_member_recent_races()` to get the latest official races for a member:

```python
# Get last 10 official races for customer_id
recent_races = client.stats_member_recent_races(cust_id=customer_id)

# Use the first entry as the "latest finished race"
latest_race = recent_races["Sessions"][0] if recent_races["Sessions"] else None
```

### b) **Subsession Result Details**
Use `result()` to get detailed results for a specific subsession (when additional fields are needed):

```python
# Get detailed results for a subsession
subsession_details = client.result(subsession_id=subsession_id)

# Extract key fields (example):
track_name = subsession_details.get("Track", {}).get("Name", "Unknown Track")
field_size = subsession_details.get("NumCars", "N/A")
series_name = subsession_details.get("Series", {}).get("Name", "Unknown Series")
```

> The library automatically handles pagination, chunked responses, and data parsing - no need to manage these low-level details.

## 3) Built-in Resilience Features
The `iracingdataapi` library includes production-ready error handling:

- **Automatic retries** with jittered backoff for transient errors (network issues, 5xx responses).
- **Rate limiting handling** - the library respects iRacing's rate limits and waits appropriately.
- **Session persistence** - cookies are maintained automatically across requests.
- **Graceful degradation** - missing fields return `None` instead of raising exceptions.

## 4) Data Model Compatibility
The library returns data in consistent Python dictionaries that map directly to your bot's needs:

- **Customer IDs**: Always treated as integers (no string parsing needed).
- **Timestamps**: Returned in UTC format (ready for your bot's timestamp formatting).
- **Nested Data**: Structured with clear hierarchy (e.g., `race["Track"]["Name"]` instead of flat key names).

## 5) Security Best Practices
- The library never logs credentials or sensitive data.
- Always store iRacing credentials in environment variables (not in code).
- Rotate credentials periodically through iRacing account settings.
- Use `silent=True` in production to avoid exposing sensitive debug information.

# LLM Engineer Playbook (You Are the Developer)

> You will write the bot in **Python** with **discord.py 2.x** (slash commands via `app_commands`), use **aiohttp** for iRacing, and **SQLite** for persistence — all inside **Docker**. No host Python.

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

## Docker
- The container must start the bot with **only** `DISCORD_TOKEN`, `IRACING_USERNAME`, `IRACING_PASSWORD`. Optional:
  - `POLL_INTERVAL_SECONDS` (default 60)
  - `LOG_LEVEL` (default INFO)
  - `SQLITE_DB_PATH` (default `/app/data/iresults.db`)

## Done Means
- Commands registered, permissions correct.
- Poller posts exactly once per race per guild+member.
- Clean shutdown, session closed, no unhandled exceptions in logs.

# Implementation Roadmap

Each stage ends with a **test & commit** gate. Keep changes small and shippable.

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
- ✅ Add structured logging with JSON format and LOG_LEVEL support
- ✅ Implement graceful shutdown handling for SIGINT/SIGTERM signals
- ✅ Add comprehensive exception guards throughout the codebase
- ✅ Implement circuit breakers for repeated API failures
- ✅ Add fallback behavior for critical failures (cached data, empty results)
- ✅ Fill `README.md` with comprehensive run instructions and documentation
- ✅ Create `docker-compose.override.example` for local development
- ✅ Update feature documentation with implementation details
- ✅ Verify Docker-only operation (no host Python required)
- ✅ **Test**: run for several hours against test `customer_id`, confirm stability
- ✅ Test edge cases (no tracked members, no config, API failures)
- ✅ Verify no unhandled exceptions in logs
- ✅ Ensure all critical events are properly logged with correlation IDs

## Optional Stage 7 — Nice-to-Haves
- Slash command `/listtracked`.
- `/help` embed with usage.
- Per-guild poll interval.
- Slash command permissions refinements.
