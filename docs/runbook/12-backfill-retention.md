# Backfill 1 year of collector data

Use this when MongoDB is running and you want to fill historical `social_items` rows instead of only collecting the newest sample.

## What it does

- Splits the last 365 days into smaller time windows.
- Calls collector adapters that support historical paging.
- Stores `collection_checkpoints` per platform/date window.
- Skips completed old windows, so reruns do not waste API calls.
- Refreshes a recent overlap window by default to catch late reviews/comments.
- Writes normalized rows into MongoDB through `persist_social_items()`.
- Reports unsupported or missing-config platforms without stopping the whole run.

Current backfill support:

| Platform | Status | Notes |
| --- | --- | --- |
| App Store | supported | RSS pages, newest-first, stops when older than window |
| Google Play | supported | `google-play-scraper` continuation tokens, newest-first |
| YouTube | supported | Data API `search.list` channel video discovery by date, then `commentThreads.list` pagination |
| Stockbit | unsupported | target URLs needed |
| X | unsupported | paid API/token/search caps needed |
| TikTok | unsupported | Research API token/approval needed |
| Instagram | unsupported | Graph API permissions/content IDs needed |
| Threads | unsupported | token/keyword approval needed |

## Prerequisites

From project root:

```bash
cd /home/hp/dev/work/bni-bions-sentiment-analysis
. .venv/bin/activate
export MONGODB_URI='mongodb://localhost:27017'
export MONGODB_DATABASE='bni_bions_sentiment'
```

Start MongoDB if needed:

```bash
/mnt/c/Program\ Files/Docker/Docker/resources/bin/docker-compose.exe up -d mongo
```

## Dry run

Collect/report without writing:

```bash
python -m pipeline.collector.backfill --dry-run --retention-days 365 --window-days 30 --limit-per-window 100
```

## Write to MongoDB

```bash
python -m pipeline.collector.backfill --retention-days 365 --window-days 30 --limit-per-window 100
```

or:

```bash
make backfill
```

## Verify MongoDB

```bash
/mnt/c/Program\ Files/Docker/Docker/resources/bin/docker-compose.exe exec -T mongo \
  mongosh --quiet bni_bions_sentiment --eval '
    print("social_items=" + db.social_items.countDocuments());
    printjson(db.social_items.aggregate([
      { $group: { _id: "$platform", count: { $sum: 1 }, oldest: { $min: "$postedAt" }, newest: { $max: "$postedAt" } } },
      { $sort: { _id: 1 } }
    ]).toArray())
  '
```

## Expected output shape

```json
{
  "app_store": {"status": "ok", "collected": 120, "inserted": 80, "windows": 13, "skipped_windows": 0},
  "google_play": {"status": "ok", "collected": 500, "inserted": 300, "windows": 13, "skipped_windows": 0},
  "youtube": {"status": "ok", "collected": 40, "inserted": 30, "windows": 13, "skipped_windows": 0}
}
```

`inserted` may be lower than `collected` because duplicate `platform + sourceId` rows are skipped.

## Tuning

- Use smaller windows if APIs time out:

```bash
python -m pipeline.collector.backfill --window-days 7 --limit-per-window 50
```

- Keep YouTube under quota with a request budget and delay:

```bash
export YOUTUBE_BACKFILL_MAX_REQUESTS=10
export YOUTUBE_BACKFILL_REQUEST_DELAY_SECONDS=2
python -m pipeline.collector.backfill --window-days 14 --limit-per-window 5
```

- Force a full refresh only when needed:

```bash
python -m pipeline.collector.backfill --refetch-existing-windows
```

Without that flag, completed platform/date checkpoints older than the recent overlap are skipped before any provider API call. The default overlap is 7 days:

```bash
python -m pipeline.collector.backfill --recent-overlap-days 7
```

- Use a shorter smoke run:

```bash
python -m pipeline.collector.backfill --retention-days 30 --window-days 7 --limit-per-window 20 --dry-run
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `mongodb connection refused` | Start MongoDB with Docker compose command above. |
| `google-play-scraper package missing` | Activate `.venv`, then install project deps. |
| `unsupported` platform | Adapter does not yet expose `collect_backfill()`. |
| `not_configured` platform | Add required env vars to `.env`; do not paste secrets into terminal output. |
| `inserted: 0` with collected rows | Rows already exist; persistence is idempotent. |

**Back:** `11-docker-mongodb.md`
