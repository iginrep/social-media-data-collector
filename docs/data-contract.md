# Canonical Social Item

```python
RawSocialItem(
  platform,
  source_type,
  source_id,
  parent_source_id,
  conversation_id,
  keyword,
  target_entity,
  author_id,
  author_username,
  author_display_name,
  text,
  language,
  source_url,
  posted_at,
  collected_at,
  metrics,
  raw_payload,
  content_hash,
)
```

Use `social_items` collection, not platform-specific one-off collections.

## Collection: social_items

Canonical normalized items. One row per review/comment.

```txt
_id                ObjectId
platform           string       "google_play" | "app_store" | "youtube"
source_type        string       "app_review" | "comment"
source_id          string       platform-specific unique ID
parent_source_id   string|null  video_id, media_id, tweet_id
conversation_id    string|null  thread/conversation root
keyword            string|null  search keyword used
target_entity      string|null  "bions", "bni_sekuritas"
author_id          string|null  platform author ID
author_username    string|null  platform username
author_display_name string|null display name
text               string       review/comment body
language           string|null  detected language
source_url         string|null  direct link to source
posted_at          string|datetime  when posted (ISO format, may have timezone offset)
collected_at       datetime     when collected
metrics            object       platform-specific (rating, thumbs_up, like_count, etc.)
raw_payload        object       full platform response for audit
content_hash       string       dedupe hash of normalized text
```

Dedupe: `platform + source_type + source_id` (primary), `platform + source_type + content_hash + parent_source_id` (fallback).

## Collection: collection_checkpoints

Backfill window status. One row per platform/date-window.

```txt
_id                ObjectId
platform           string       "google_play" | "app_store" | "youtube"
windowStart        datetime     ISO window start
windowEnd          datetime     ISO window end
status             string       "complete" | "partial"
collectedCount     int          items fetched from API
insertedCount      int          items written to social_items
errorMessage       string|null  error if stopped
createdAt          datetime     first attempt
completedAt        datetime|null completion timestamp
```

Unique index: `platform + windowStart + windowEnd`.

Behavior:
- complete old windows → skip API call on rerun
- partial windows → resume from last checkpoint
- recent overlap (7d) → re-collect to catch late reviews
- `--refetch-existing-windows` overrides all checkpoints
