# Functional Specification (Non‑Technical)

## 1. Purpose
A Discord bot that **tracks iRacing race results** for selected drivers and **posts them automatically** to a designated Discord channel. Users manage tracking with **three slash commands** preserved from the reference project:
- `/lastrace customer_id:<id>` — on-demand: show the latest official race result for a specific iRacing member.
- `/setchannel channel:<#channel>` — admin-only: set the channel where auto-posted results will appear.
- `/trackmember customer_id:<id>` — add a member (by iRacing Customer ID) to the bot’s tracking list for the current server.

The bot operates in the background, polling iRacing for new finished races for tracked members and posting a summary when a new result appears.

## 2. In-Scope Features
- **Slash commands** (exact names/params as above).
- **Per-server tracking lists** (each Discord guild maintains its own set of tracked members).
- **Auto-posting**: when a tracked member finishes an official race, post a single digest message to the configured channel.
- **De-duplication**: a race result is posted **once** per guild+member.
- **Persistence**: tracking lists, configured channel, and last-posted race IDs survive restarts (SQLite file).

## 3. Out-of-Scope (MVP)
- Real-time lap-by-lap telemetry, live “race started” notifications, or deep analytics.
- Cross-platform messaging (Telegram/Slack/etc.).
- User authentication flows beyond Discord bot identity.
- Arbitrary iRacing data browsing beyond what’s required to post latest results.
- Moderation systems, permissions beyond what’s needed for `/setchannel` (admin).

## 4. Users & Roles
- **Server Admins** — can run all commands; `/setchannel` requires guild admin permission.
- **Regular Members** — can use `/lastrace` to fetch last result for any customer_id; may be allowed to use `/trackmember` (policy is configurable but default is **allow**).

## 5. Command Behaviors (UX)
### `/trackmember customer_id:<id>`
- Adds the member to this guild’s tracking list.
- If already tracked, respond with an idempotent confirmation.
- Success message example: “Member **123456** is now being tracked in this server.”

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
