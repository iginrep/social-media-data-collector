# Collector contract

Every collector must be swappable, low-risk by default, and normalize output into the canonical social item shape.

## Adapter responsibilities

A collector adapter should:

1. accept a keyword/source config.
2. fetch public data within configured limits.
3. stop safely on auth/rate/captcha/private-content signals.
4. normalize platform payloads into `RawSocialItem`.
5. preserve raw payload for audit, subject to redaction/retention.
6. attach provenance fields.
7. return deterministic items without live DB side effects where possible.

## Canonical item

```python
RawSocialItem(
  platform: str,
  source_type: str,
  source_id: str,
  parent_source_id: str | None,
  conversation_id: str | None,
  keyword: str | None,
  target_entity: str | None,
  author_id: str | None,
  author_username: str | None,
  author_display_name: str | None,
  text: str,
  language: str | None,
  source_url: str | None,
  posted_at: datetime | None,
  collected_at: datetime,
  metrics: dict,
  raw_payload: dict,
  content_hash: str,
)
```

## Required provenance

```json
{
  "collectionMethod": "official_api | unofficial_api | automation | rss | vendor",
  "accessRisk": "low | medium | high",
  "collectorVersion": "v0.1"
}
```

## Platform mappings

### Google Play

```yaml
platform: google_play
source_type: app_review
collectionMethod: unofficial_api
accessRisk: medium
app_id: id.bions.bnis.android
country: id
language: id
```

Expected fields:

```txt
reviewId -> source_id
userName -> author_username/display_name
content -> text
score -> metrics.rating
thumbsUpCount -> metrics.thumbs_up
reviewCreatedVersion/appVersion -> metrics.app_version or raw_payload
at -> posted_at
```

### Apple App Store

```yaml
platform: app_store
source_type: app_review
collectionMethod: rss
accessRisk: low
app_id: "6736508566"
country: id
```

Expected fields:

```txt
review id -> source_id
author -> author_username/display_name
title + content -> text
rating -> metrics.rating
updated -> posted_at
version -> metrics.app_version or raw_payload
```

### YouTube

```yaml
platform: youtube
source_type: comment
collectionMethod: official_api
accessRisk: low
auth_env: YOUTUBE_API_KEY
channels:
  - BNI1946
  - bnisekuritas46
```

Expected fields:

```txt
comment_id -> source_id
video_id -> parent_source_id/conversation_id
authorDisplayName -> author_display_name
authorChannelId -> author_id
textOriginal -> text
likeCount -> metrics.like_count
totalReplyCount -> metrics.reply_count
publishedAt/updatedAt -> posted_at/raw_payload
```

## Backfill contract

Adapters that support historical collection should also implement `collect_backfill()`:

```python
def collect_backfill(
    self,
    keyword: str,
    target_entity: str,
    since: datetime,
    until: datetime,
    limit: int = 50,
) -> list[RawSocialItem]: ...
```

This is optional. Adapters without it are marked `unsupported` by the backfill runner.

### Rate-limit and quota safety

Backfill supports per-run request budgets and delays:

```txt
YOUTUBE_BACKFILL_MAX_REQUESTS          per-run hard cap (default: no limit)
YOUTUBE_BACKFILL_REQUEST_DELAY_SECONDS delay between API calls (default: 0)
```

When the budget is exhausted, the adapter raises `CollectorStopped`. The runner marks the window as `partial` and exits gracefully. No data is lost; rerun resumes from checkpoint.

### Checkpoint store

Backfill uses `BackfillCheckpointStore` (Protocol in `backfill.py`) backed by `MongoBackfillCheckpointStore` in `pipeline/storage/backfill_checkpoints.py`.

```txt
collection_checkpoints
  platform          string
  windowStart       datetime (ISO)
  windowEnd         datetime (ISO)
  status            "complete" | "partial"
  collectedCount    int
  insertedCount     int
  errorMessage      string | null
  createdAt         datetime
  completedAt       datetime | null
```

Unique index: `platform + windowStart + windowEnd`.

Behavior:
- complete old windows → skip API call
- partial windows → resume
- recent overlap (default 7 days) → re-collect
- `--refetch-existing-windows` overrides all checkpoints

## Dedupe

Priority:

1. `platform + source_type + source_id`
2. fallback `platform + source_type + content_hash + parent_source_id`

Hash normalized text, not raw payload.

## Testing contract

Each adapter should have tests for:

- normal payload.
- empty payload.
- missing optional fields.
- duplicate payload.
- malformed payload.
- stop condition mapping.
- no live network required in unit tests.

## Do not implement

Do not add new high-risk scraping behavior while implementing this contract. Keep Stockbit/X/TikTok/Instagram/Threads adapters as disabled stubs until separately approved.
