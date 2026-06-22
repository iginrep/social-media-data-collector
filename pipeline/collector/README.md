# collector pipeline

Platform collection layer for public BNI/BIONS feedback.

## Purpose

Collectors fetch source-specific data and normalize it into `RawSocialItem` from `pipeline/collector/base.py`.

## Canonical model

Important fields:

```txt
platform
source_type
source_id
keyword
target_entity
text
author_id
author_username
author_display_name
language
source_url
posted_at
collected_at
metrics
raw_payload
content_hash
collection_method
access_risk
collector_version
```

## Adapter contract

Each adapter implements:

```python
collect(keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]
```

Adapters supporting historical backfill also implement:

```python
collect_backfill(keyword: str, target_entity: str, since: datetime, until: datetime, limit: int = 50) -> list[RawSocialItem]
```

Adapter metadata:

```txt
platform
access_mode
cost_level
risk_level
enabled_by_default
```

## Approved enabled sources

| Adapter | Source | Default | Backfill |
| --- | --- | --- | --- |
| `google_play.py` | BIONS Google Play reviews | enabled | yes |
| `app_store.py` | BIONS Apple App Store reviews | enabled | yes |
| `youtube.py` | approved BNI/BIONS YouTube channels | enabled with `YOUTUBE_API_KEY` | yes |

## Disabled risky sources

| Adapter | Reason |
| --- | --- |
| `stockbit.py` | likely login/session automation. |
| `twitter.py` | official paid path or high-risk unofficial scraping. |
| `tiktok.py` | unstable public access, CAPTCHA risk. |
| `instagram.py` | login/API limitations. |
| `threads.py` | limited public discovery/API. |

Do not enable disabled adapters without explicit current-task approval.

## Backfill

Run historical backfill with checkpoint-based resume:

```bash
# dry-run (no writes)
python -m pipeline.collector.backfill --dry-run --retention-days 365 --window-days 14

# live backfill
python -m pipeline.collector.backfill --retention-days 365 --window-days 14 --limit-per-window 5 --recent-overlap-days 7

# force full re-collect
python -m pipeline.collector.backfill --refetch-existing-windows
```

Checkpoint store: `pipeline/storage/backfill_checkpoints.py` → `collection_checkpoints` collection.

Social items persistence: `pipeline/storage/social_items.py` → `social_items` collection.

## Stop conditions

Stop on 401/403, 429, CAPTCHA, login wall, quota exhaustion, private/deleted content, or repeated server failures.

## Tests

```bash
. .venv/bin/activate
pytest -q tests/unit/pipeline/collector/
```
