# Run All Collectors

Use the runner to collect from all configured platforms at once.

## Quick start

```bash
. .venv/bin/activate
python3 -m pipeline.collector.run
```

This runs every collector that has its env vars configured. Collectors missing tokens are skipped with a `not_configured` status.

## What happens

1. **Validation check** -- the runner checks which platforms have their env vars set
2. **Collection** -- each configured platform fetches data
3. **Report** -- prints a summary of what was collected

## Example output

```
--- config validation ---
  app_store: READY
  google_play: READY
  youtube: READY
  x: MISSING: ['X_BEARER_TOKEN']
  tiktok: MISSING: ['TIKTOK_RESEARCH_ACCESS_TOKEN', 'TIKTOK_VIDEO_IDS']
  instagram: MISSING: ['INSTAGRAM_GRAPH_ACCESS_TOKEN']
  threads: MISSING: ['THREADS_ACCESS_TOKEN']
  stockbit: MISSING: ['STOCKBIT_TARGET_URLS']

--- collected ---
  app_store: 10
  google_play: 10
  youtube: 10
```

## Customize the runner

### Include risky collectors (Stockbit, etc.)

```python
from pipeline.collector.run import collect_sample

items = collect_sample(include_risky=True)
print(f"Total: {len(items)}")
```

### Collect more items

```python
from pipeline.collector.run import collect_sample

items = collect_sample(limit=100)
```

### Save to database

```python
from pipeline.collector.run import collect_sample

items = collect_sample(write=True)
```

This writes items to MongoDB using idempotent upserts (no duplicates).

## What each platform returns (default limits)

| Platform | Default limit | Notes |
| --- | --- | --- |
| App Store | 10 reviews | RSS, paginated |
| Google Play | 10 reviews | Scraper |
| YouTube | 10 items | Videos + comments (if API key set) |
| X/Twitter | 10 tweets | Needs Basic tier ($100/mo) |
| TikTok | 10 items | oembed or Research API |
| Instagram | 10 comments | Graph API only |
| Threads | 10 replies | Threads API only |
| Stockbit | 10 pages | Public scrape, high risk |

## Troubleshooting

| Problem | Fix |
| --- | ---|
| All platforms show `MISSING` | You haven't configured any env vars. See [Prerequisites](00-prerequisites.md) |
| Only some platforms run | The others need their env vars. Check the validation output |
| `ModuleNotFoundError` | Run `pip install -e '.[dev]'` and `pip install -e '.[collectors]'` |
| Slow collection | Each platform has network delays. Total time depends on how many are configured |

---

**Back:** [08 - Stockbit](08-stockbit.md) | **Next:** [10 - Troubleshooting](10-troubleshooting.md)
