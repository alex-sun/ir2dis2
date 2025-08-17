# Implementation Roadmap

Each stage ends with a **test & commit** gate. Keep changes small and shippable.

## Stage 0 — Repo & Bootstrap (commit: init)
- Create repo with `bootstrap/` content (copy & adapt).
- Fill `.env` from `.env.example`.
- Build & run container (bot will just print “starting” until code exists).

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
