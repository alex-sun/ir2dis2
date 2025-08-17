# iRacing Data API – Practical Integration Notes

> This guide summarizes what the bot needs from iRacing’s “/data” API to find and post **latest official race results** for a member.

## 1) Authentication
- Authenticate against **`https://members-ng.iracing.com/auth`** with your iRacing credentials (email + password).
- On success you receive cookies/tokens used for subsequent **`/data/*`** requests.
- If your account uses 2FA, enable **Legacy Read Only Authentication** in account settings to allow script access to the Data API without a second factor (until OAuth is available).
- Keep the session cookie in an HTTP client session; refresh/re-login on **401 Unauthorized**.

## 2) Endpoints You’ll Use Most
### a) **Recent races for a member**
- **`GET /data/stats/member_recent_races?cust_id={customer_id}`**
- Returns the **last 10 official races** for the member. Use the first entry as the “latest finished race”.

### b) **Session/Subsession results (details)**
- **`GET /data/results/get?subsession_id={subsession_id}`**
- Returns result details for a subsession (race), including positions, field size, track, series, etc.
- Call this **only when** you need fields not present in the “recent races” response (to reduce load).

> Other useful lookups exist (cars, tracks, series), but the two endpoints above are sufficient for MVP posting.

## 3) Polling Strategy
- Poll **only** the tracked members, on a configurable interval (e.g., 60s).
- Cache/store the **last published `subsession_id`** per guild+member to avoid duplicate posts.
- Stagger requests across members to avoid burst traffic.

## 4) Error Handling & Backoff
- Treat network and 5xx as transient; retry with jittered backoff.
- Treat 401 as “session expired”; attempt re-auth once, then log and continue.
- Rate limiting: if observed, slow down polling interval and log a warning.

## 5) Data Hygiene
- Customer IDs are integers (`cust_id`). Accept them verbatim from commands.
- Timestamps from API are typically UTC; format consistently in messages.
- Be robust to missing fields; prefer omission over “None/NaN” text.

## 6) Security
- Do **not** log credentials or raw cookies.
- Keep secrets in env vars; never commit them.
- Rotate credentials when staff changes.
