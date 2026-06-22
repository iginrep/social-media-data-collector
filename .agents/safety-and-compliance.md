# Safety and compliance rules

Safety wins over volume.

## Hard bans

Do not do these unless the user explicitly approves in the current task:

- enable Stockbit/X/TikTok/Instagram/Threads collectors.
- log into any third-party account.
- import cookies, browser profiles, session tokens, or local storage.
- bypass CAPTCHA, bot checks, rate limits, login walls, or content access controls.
- scrape private/deleted/login-only content.
- use personal accounts for automation.
- send collected data to a paid vendor.
- commit secrets or raw collected data.

## Stop rules

Stop current platform run immediately on:

```txt
401/403 auth or permission errors
429 rate limits
CAPTCHA or anti-bot page
login wall or forced relogin
3 consecutive 5xx errors
quota budget exceeded
private/deleted/login-only marker
duplicate rate >80% after first page
```

After stop, write a clear error/status record. Do not retry aggressively.

## Safe default parameters

```yaml
schedule: "1x/day initially"
timezone: Asia/Jakarta
initial_backfill_days: 30
rolling_backfill_days: 7
raw_retention_days: 180
aggregate_retention_days: 365

google_play:
  max_items_per_run: 100
  rate_limit: "1 request / 5-10 sec"
  max_pages: 5

apple_app_store:
  max_items_per_run: 100
  rate_limit: "1 request / 5-10 sec"

youtube:
  max_comments_per_run: 200
  max_videos_per_run: 50
  daily_quota_budget_units: 500
  avoid_search_list_in_routine_runs: true
```

After 14 clean days, user can approve higher caps.

## YouTube quota safety

Use approved channels first. Avoid broad `search.list` in routine runs because it costs much more quota.

Preferred flow:

```txt
channel handle/url
  -> resolve channel id/uploads playlist
  -> playlistItems.list recent videos
  -> commentThreads.list comments
```

Budget:

```txt
commentThreads.list = low cost
playlistItems.list = low cost
search.list = expensive, avoid routine use
collector daily budget <= 500 units
stop at 80% budget
```

## Privacy rules

User approved saving public usernames/display names.

Still redact these before persistence/export when detected:

```txt
email addresses
phone numbers
KTP/NIK-like numbers
bank/account/card-like numbers
passwords/secrets/tokens
private addresses
```

Do not export usernames unless needed for analysis. Prefer aggregate reports.

Raw retention: 180 days.

Aggregates/sentiment retention: 365 days by default.

Support deletion by platform + source id/hash.

## Backfill safety

```yaml
backfill:
  default_retention_days: 365
  default_window_days: 14
  default_recent_overlap_days: 7
  checkpoint_skip_complete_old_windows: true
  youtube_backfill_max_requests: set per run (default: no limit)
  youtube_backfill_request_delay_seconds: 2
  dry_run_writes_no_checkpoints: true
  stop_on_quota_exhaustion: true
```

Checkpoint behavior:
- complete old windows → skip API (no wasted calls)
- partial windows → resume from last checkpoint
- recent overlap (7d default) → re-collect to catch late reviews
- `--refetch-existing-windows` forces full re-run
- `--dry-run` collects and reports without writing checkpoints or data

## Git safety

Never commit:

```txt
.env
*.pem
cookies
browser profiles
raw data dumps
data/raw/*
data/processed/*
data/exports/*
API keys
tokens
passwords
connection strings
```

Before commit:

```bash
git diff --staged | grep -Ei 'password|secret|api[_-]?key|token|cookie|authorization|bearer' || true
```

Real secrets must block commit. Placeholder docs are ok.
