# Instagram Collector

Two official lanes available:
- owned content comments: comments and replies under media IDs you provide
- hashtag discovery: public media for approved hashtags, then comments under discovered media

Public HTTP helper still exists for metadata-only experiments, but it cannot fetch comments.

## What it collects

### owned content comments
- Comment text, author username, timestamp
- Reply threads on comments
- Flat thread fields: `root_source_id`, `parent_source_id`, `depth`, `relation_type`

### hashtag discovery
- Public media tagged with configured hashtags
- Caption, permalink, media type, timestamp, comment count, like count
- Comments and replies under discovered media

## Prerequisites

- Virtual environment activated. See [Prerequisites](00-prerequisites.md)
- Instagram Business or Creator account connected to a Facebook Page
- User access token with needed Instagram permissions

## Env vars

```env
INSTAGRAM_GRAPH_ACCESS_TOKEN=***

# lane 1. owned content comments
INSTAGRAM_MEDIA_IDS=1789012345678901234,1789012345678905678

# lane 2. hashtag discovery
INSTAGRAM_IG_USER_ID=17841405309211844
INSTAGRAM_HASHTAG_QUERIES=BIONS,BNISEKURITAS
```

At least one lane must be configured:
- `INSTAGRAM_MEDIA_IDS`
- or `INSTAGRAM_IG_USER_ID` + `INSTAGRAM_HASHTAG_QUERIES`

## How to get token and IDs

1. Go to `https://developers.facebook.com/`
2. Create/select a Business app
3. Add Instagram Graph API
4. Generate a token in Graph API Explorer
5. Add permissions needed for your lane:
   - owned comments: `instagram_basic`, `instagram_manage_comments`
   - hashtag discovery: `instagram_basic` plus Instagram Public Content Access approval
6. Find media IDs:

```txt
GET /me/media?fields=id,caption,timestamp
```

7. Find Instagram user ID if needed:

```txt
GET /me/accounts
GET /{page_id}?fields=instagram_business_account
```

## How hashtag lane works

For each query in `INSTAGRAM_HASHTAG_QUERIES`:

```txt
GET /{IG_USER_ID}/ig_hashtag_search?user_id={IG_USER_ID}&q=BIONS
GET /{HASHTAG_ID}/recent_media?user_id={IG_USER_ID}&fields=id,caption,media_type,permalink,timestamp,comments_count,like_count
GET /{MEDIA_ID}/comments?fields=id,text,timestamp,username,replies{id,text,timestamp,username}
```

Source: `https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-hashtag/recent-media`

Limits:
- only public photos/videos
- recent media only covers media within 24h of query time
- max 50 results per page
- max 30 unique hashtags per 7 days
- `username` is not available on hashtag media results

## Run it

```bash
python3 -m pipeline.collector.run
```

Or from Python:

```python
from pipeline.collector.adapters.instagram import InstagramAdapter

rows = InstagramAdapter().collect("bions", "bions", limit=50)
```

## Output examples

Hashtag media row:

```json
{
  "platform": "instagram",
  "source_type": "post",
  "source_id": "1789012345678901234",
  "root_source_id": "1789012345678901234",
  "depth": 0,
  "relation_type": "mention",
  "keyword": "BIONS",
  "collection_method": "official_instagram_hashtag_search"
}
```

Comment row:

```json
{
  "platform": "instagram",
  "source_type": "comment",
  "source_id": "1789012345678909999",
  "root_source_id": "1789012345678901234",
  "depth": 1,
  "relation_type": "comment",
  "collection_method": "official_graph_api"
}
```

Reply row:

```json
{
  "platform": "instagram",
  "source_type": "comment",
  "source_id": "1789012345678911111",
  "root_source_id": "1789012345678901234",
  "parent_source_id": "1789012345678909999",
  "depth": 2,
  "relation_type": "reply",
  "collection_method": "official_graph_api"
}
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `INSTAGRAM_GRAPH_ACCESS_TOKEN missing` | Add token to `.env` |
| `INSTAGRAM_MEDIA_IDS or INSTAGRAM_HASHTAG_QUERIES missing` | Configure at least one lane |
| `INSTAGRAM_IG_USER_ID missing` | Required for hashtag discovery |
| 401 Unauthorized | Token expired or invalid |
| 403 Forbidden | Permission or app approval missing |
| 429 Rate limit | Stop and retry later |
| Empty hashtag results | No recent public media, hashtag blocked, or query too narrow |

---

**Next:** [07 - Threads](07-threads.md) | **Back:** [05 - TikTok](05-tiktok.md)
