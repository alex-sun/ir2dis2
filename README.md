# Bootstrap Skeleton (No App Code)

This folder gives you a **container-first** starting point for the Python implementation.

## Quick Start (after you add the app code)
1. Copy `.env.example` to `.env` and fill values.
2. `docker compose up --build`
3. Invite the bot to your test server, then run:
   - `/setchannel #results`
   - `/trackmember customer_id:123456`
   - `/lastrace customer_id:123456`

## Notes
- The SQLite database is stored under `/app/data` inside the container. Bind-mount a host directory if you want it to persist across rebuilds.
- Do not commit real secrets. `.env` is git-ignored.
