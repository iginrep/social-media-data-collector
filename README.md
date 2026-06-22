# BNI/BIONS Sentiment Analysis

A cheapest-first, safety-first monitoring system for public feedback about BNI Sekuritas and the BIONS app.

The project collects public app reviews and social comments, normalizes them into one canonical data model, classifies sentiment, then exposes results through API, dashboard, and exports.

## What this solves

BNI/BIONS teams need a repeatable way to see:

- what users complain about in the BIONS app.
- whether sentiment is improving or worsening.
- which topics drive negative feedback: login, OTP, trading, deposits, withdrawals, fees, app stability, performance, customer service.
- which data sources are useful enough to justify paid APIs/vendors later.

## Current strategy

Cheapest-first validation.

1. Start with public/free low-risk sources.
2. Keep risky platforms disabled by default.
3. Build a stable collector + sentiment + reporting pipeline.
4. Upgrade to official paid APIs/vendors only after a source proves value.

Approved MVP sources:

| Source | Target | Status | Risk |
| --- | --- | --- | --- |
| Google Play | `id.bions.bnis.android` | enabled | low/medium |
| Apple App Store | app id `6736508566` | enabled | low |
| YouTube | `@BNI1946`, `@bnisekuritas46` | enabled, needs `YOUTUBE_API_KEY` | low |
| Stockbit | BNI/BIONS terms | disabled | high |
| X/Twitter | BNI/BIONS terms | disabled | high |
| TikTok | BNI/BIONS terms | disabled | high |
| Instagram | BNI/BIONS terms | disabled | high |
| Threads | BNI/BIONS terms | disabled | high |

## Architecture

```txt
keywords + schedules
  -> collector adapters
  -> RawSocialItem normalization
  -> dedupe + preprocessing
  -> sentiment classification
  -> MongoDB
  -> FastAPI
  -> dashboard + exports
```

Core modules:

| Path | Purpose |
| --- | --- |
| `apps/api/` | FastAPI service for health, comments, sentiment, exports, keywords, schedules. |
| `apps/dashboard/` | Next.js dashboard scaffold. |
| `pipeline/collector/` | Platform adapters, canonical data model, normalization, dedupe, backfill runner. |
| `pipeline/storage/` | Social items persistence, checkpoint store for backfill. |
| `pipeline/sentiment/` | Text preprocessing, rule-based sentiment, future model hooks. |
| `pipeline/scheduler/` | Scheduled collector/analyzer jobs. |
| `pipeline/export/` | CSV/XLSX export helpers. |
| `db/` | MongoDB init, indexes, seed keywords, legacy SQL notes. |
| `docs/` | Human-facing strategy, architecture, contracts, research. |
| `.agents/` | AI-agent project context and operating rules. |

## Quick start

```bash
cd /home/hp/dev/work/bni-bions-sentiment-analysis
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
make mongo-up
pytest -q
```

Optional collector deps:

```bash
pip install -e '.[collectors]'
```

Run pipeline pieces:

```bash
make collect
make analyze
make export
make api
make backfill
```

Equivalent direct commands:

```bash
python3 -m pipeline.collector.run
python3 -m pipeline.sentiment.run
python3 -m pipeline.export.csv_export
python3 -m uvicorn apps.api.app.main:app --reload
```

## Configuration

Local secrets belong in `.env`. Do not commit `.env`.

Required when using YouTube collector:

```env
YOUTUBE_API_KEY=...
```

Default runtime settings are currently defined in `apps/api/app/config.py`:

```txt
APP_TIMEZONE=Asia/Jakarta
SENTIMENT_METHOD=rule_based
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=bni_bions_sentiment
```

Local MongoDB:

```bash
make mongo-up
make mongo-status
```

## Safe operating defaults

Use these until there are 14 clean days of successful runs:

```yaml
global:
  schedule: "1x/day"
  timezone: Asia/Jakarta
  initial_backfill_days: 30
  rolling_backfill_days: 7
  raw_retention_days: 180
  aggregate_retention_days: 365

google_play:
  max_items_per_run: 100
  rate_limit: "1 request / 5-10 sec"

apple_app_store:
  max_items_per_run: 100
  rate_limit: "1 request / 5-10 sec"

youtube:
  max_comments_per_run: 200
  max_videos_per_run: 50
  daily_quota_budget_units: 500
```

Stop collection on auth errors, rate limits, CAPTCHA, login walls, quota budget exhaustion, private/deleted content, or repeated server failures.

## Data model

All collectors should emit `RawSocialItem` from `pipeline/collector/base.py`.

Important fields:

```txt
platform
source_type
source_id
keyword
target_entity
text
author_username
author_display_name
posted_at
collected_at
metrics
raw_payload
content_hash
collection_method
access_risk
collector_version
```

User approved saving public usernames/display names. Still redact secrets, emails, phone numbers, NIK/KTP-like values, account/card-like numbers, and passwords from stored/exported data.

## Documentation map

Start here:

| Document | Use |
| --- | --- |
| `AGENTS.md` | AI coding agent entrypoint. |
| `.agents/README.md` | AI-agent doc map. |
| `docs/architecture.md` | System architecture explanation. |
| `docs/data-contract.md` | Canonical item reference. |
| `docs/collector-strategy.md` | Collector plan and source priorities. |
| `docs/provider-decision-matrix.md` | Source/vendor tradeoffs. |
| `docs/human-approval-checklist.md` | Approved sources and risk gates. |
| `docs/labeling-guideline.md` | Sentiment labeling guide. |

## Runbook

Step-by-step guides for running each collector.

| Guide | What it covers |
| --- | --- |
| [00 - Prerequisites](docs/runbook/00-prerequisites.md) | Setup: Python, venv, install, .env config |
| [01 - Google Play](docs/runbook/01-google-play.md) | Collect app reviews (no API key) |
| [02 - App Store](docs/runbook/02-app-store.md) | Collect app reviews (no API key) |
| [03 - YouTube](docs/runbook/03-youtube.md) | Collect video comments (needs API key) |
| [04 - X/Twitter](docs/runbook/04-x-twitter.md) | Collect mentions + replies (needs bearer token) |
| [05 - TikTok](docs/runbook/05-tiktok.md) | Collect video comments (needs research token) |
| [06 - Instagram](docs/runbook/06-instagram.md) | Collect post comments (needs graph token) |
| [07 - Threads](docs/runbook/07-threads.md) | Collect thread replies (needs access token) |
| [08 - Stockbit](docs/runbook/08-stockbit.md) | Collect discussions (public scrape, high risk) |
| [09 - Run All](docs/runbook/09-run-all.md) | Run all collectors at once |
| [10 - Troubleshooting](docs/runbook/10-troubleshooting.md) | Common errors and fixes |
| [11 - Docker MongoDB](docs/runbook/11-docker-mongodb.md) | Local MongoDB infra for collector storage |
| [12 - Backfill Retention](docs/runbook/12-backfill-retention.md) | Fill 1 year of historical collector data into MongoDB |

## Development workflow

Before claiming work complete:

```bash
. .venv/bin/activate
pytest -q
node --check db/mongo-init.js
git diff --check
```

Before commit, scan staged diff for accidental secrets:

```bash
git diff --staged | grep -Ei 'password|secret|api[_-]?key|token|cookie|authorization|bearer' || true
```

## Current limitations

- Backfill works for Google Play, App Store, and YouTube. X/Instagram/Threads/TikTok/Stockbit require historical adapter implementation.
- Risky social sources are intentionally disabled for live collection.
- Sentiment is currently rule-based and should be improved with labeled Indonesian finance/app-review examples.
- `db/schema.sql` and `db/seed_keywords.sql` are legacy SQL references while the active database target is MongoDB.

## License

Internal project scaffold unless a license is added.
