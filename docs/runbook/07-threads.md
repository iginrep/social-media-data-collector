# Threads Collector

Two official lanes available:
- owned thread conversations: full conversation for media IDs you provide
- keyword search: public Threads posts matching configured keywords

Public HTTP helper still exists for metadata-only experiments, but it cannot fetch replies.

## What it collects

### owned thread conversations
- Original post plus replies
- Native tree fields from Threads API: `root_post`, `replied_to`, `is_reply`
- Normalized flat thread fields: `root_source_id`, `parent_source_id`, `depth`, `relation_type`

### keyword search
- Public posts matching keywords
- Text, username, permalink, timestamp, media type
- `has_replies`, `is_quote_post`, `is_reply` metadata

## Prerequisites

- Virtual environment activated. See [Prerequisites](00-prerequisites.md)
- Threads API access token

## Env vars

```env
THREADS_ACCESS_TOKEN=***

# lane 1. owned conversations
THREADS_MEDIA_IDS=1789012345678901234,1789012345678905678

# lane 2. public keyword search
THREADS_SEARCH_QUERIES=BIONS,BNI Sekuritas,BIONS error
```

At least one lane must be configured:
- `THREADS_MEDIA_IDS`
- or `THREADS_SEARCH_QUERIES`

## Permissions

- `threads_basic`: required for Threads API calls
- `threads_read_replies`: needed for conversation/replies lane
- `threads_keyword_search`: needed for public keyword search

Without `threads_keyword_search` approval, search only covers posts owned by the authenticated user. After approval, public posts are searchable.

## How keyword lane works

For each query in `THREADS_SEARCH_QUERIES`:

```txt
GET https://graph.threads.net/v1.0/keyword_search
  ?q=BIONS
  &search_type=RECENT
  &fields=id,text,media_type,permalink,timestamp,username,has_replies,is_quote_post,is_reply
  &limit=50
```

Source: `https://developers.facebook.com/docs/threads/keyword-search/`

Useful params supported by API:
- `q`: required keyword
- `search_type`: `TOP` or `RECENT`
- `search_mode`: `KEYWORD` or `TAG`
- `media_type`: `TEXT`, `IMAGE`, `VIDEO`
- `since`, `until`: time bounds
- `limit`: default 25, max 100
- `author_username`: exact username filter without `@`

Limits:
- 2,200 queries per rolling 24h per user across apps
- no-result queries do not count
- sensitive/offensive queries may return empty array
- `owner` field excluded

## Run it

```bash
python3 -m pipeline.collector.run
```

Or from Python:

```python
from pipeline.collector.adapters.threads import ThreadsAdapter

rows = ThreadsAdapter().collect("bions", "bions", limit=50)
```

## Output examples

Keyword search post:

```json
{
  "platform": "threads",
  "source_type": "post",
  "source_id": "1234567890",
  "root_source_id": "1234567890",
  "conversation_id": "1234567890",
  "depth": 0,
  "relation_type": "mention",
  "keyword": "BIONS",
  "collection_method": "official_threads_keyword_search"
}
```

Conversation reply:

```json
{
  "platform": "threads",
  "source_type": "reply",
  "source_id": "1789012345678909999",
  "root_source_id": "1789012345678901234",
  "parent_source_id": "1789012345678901234",
  "depth": 1,
  "relation_type": "reply",
  "collection_method": "official_threads_api"
}
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `THREADS_ACCESS_TOKEN missing` | Add token to `.env` |
| `THREADS_MEDIA_IDS or THREADS_SEARCH_QUERIES missing` | Configure at least one lane |
| Search only returns own posts | App lacks `threads_keyword_search` approval |
| 401 Unauthorized | Token expired or invalid |
| 403 Forbidden | Permission or app approval missing |
| 429 Rate limit | Stop and retry later |
| Empty search results | Query may be sensitive, too narrow, or no public matches |

---

**Next:** [08 - Stockbit](08-stockbit.md) | **Back:** [06 - Instagram](06-instagram.md)
